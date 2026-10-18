"""AI behaviour: fallbacks, validation of model output, and review analysis."""
import json

from models import Product
from services import gemini_service
from services.gemini_service import GeminiError


def _ids(app, *skus):
    return [Product.query.filter_by(sku=s).first().id for s in skus]


# ---- Recommendations ------------------------------------------------------ #
def test_recommendations_fallback_without_key(client):
    r = client.post("/api/recommendations", json={"query": "best headphones under ₹3,000"})
    body = r.get_json()
    assert r.status_code == 200
    assert body["source"] == "rules" and body["ai_generated"] is False
    assert body["fallback_reason"] == "ai_not_configured"
    assert "not Gemini" in body["notice"]
    assert body["items"]
    for item in body["items"]:
        assert item["product"]["category"] == "Headphones"
        assert item["product"]["price"] <= 3000
        assert item["product_id"] == item["product"]["id"]


def test_recommendations_laptop_budget(client):
    items = client.post("/api/recommendations",
                        json={"query": "laptop for programming under ₹60,000"}).get_json()["items"]
    assert items and items[0]["product"]["sku"] == "LP-001"
    assert all(i["product"]["price"] <= 60000 for i in items)


def test_recommendations_validation(client):
    assert client.post("/api/recommendations", json={}).status_code == 400
    assert client.post("/api/recommendations", json={"query": "  "}).status_code == 400
    assert client.post("/api/recommendations", json={"query": "x" * 501}).status_code == 400
    assert client.post("/api/recommendations",
                       json={"query": "phone", "limit": 99}).status_code == 400


def test_recommendations_gemini_rejects_unknown_ids(app, client, configured_gemini, monkeypatch):
    real = _ids(app, "HP-001")[0]
    payload = {"recommendations": [
        {"product_id": 99999, "reason": "invented", "strengths": [], "limitations": [],
         "budget_fit": "x"},
        {"product_id": real, "reason": "Strong bass at a low price.",
         "strengths": ["Deep bass"], "limitations": ["Mic is average"], "budget_fit": "ok"},
    ]}
    monkeypatch.setattr(gemini_service, "_call_model", lambda p, json_mode: json.dumps(payload))
    body = client.post("/api/recommendations",
                       json={"query": "headphones under 3000"}).get_json()
    assert body["source"] == "gemini" and body["ai_generated"] is True
    assert [i["product_id"] for i in body["items"]] == [real]
    assert body["items"][0]["product"]["price"] == 1799  # price comes from DB


def test_recommendations_gemini_drops_invented_prices(app, client, configured_gemini, monkeypatch):
    real = _ids(app, "HP-001")[0]
    payload = {"recommendations": [{
        "product_id": real, "reason": "Now only ₹999 with a huge discount!",
        "strengths": ["Costs ₹999", "Deep bass"], "limitations": [], "budget_fit": "great"}]}
    monkeypatch.setattr(gemini_service, "_call_model", lambda p, json_mode: json.dumps(payload))
    item = client.post("/api/recommendations",
                       json={"query": "earbuds under 3000"}).get_json()["items"][0]
    assert "999" not in json.dumps(item["reasons"] + item["strengths"])


def test_recommendations_fall_back_on_api_error(client, configured_gemini, monkeypatch):
    def boom(prompt, json_mode):
        raise GeminiError("rate limited")
    monkeypatch.setattr(gemini_service, "_call_model", boom)
    body = client.post("/api/recommendations", json={"query": "phone under 20000"}).get_json()
    assert body["source"] == "rules" and body["ai_generated"] is False
    assert body["fallback_reason"] == "ai_error" and body["items"]


def test_recommendations_fall_back_on_malformed_json(client, configured_gemini, monkeypatch):
    monkeypatch.setattr(gemini_service, "_call_model", lambda p, json_mode: "not json {")
    body = client.post("/api/recommendations", json={"query": "laptop"}).get_json()
    assert body["source"] == "rules" and body["fallback_reason"] == "ai_error"


# ---- Compare -------------------------------------------------------------- #
def test_compare_fallback_and_table(app, client):
    ids = _ids(app, "HP-001", "HP-002")
    r = client.post("/api/compare", json={"product_ids": ids})
    body = r.get_json()
    assert r.status_code == 200
    assert body["source"] == "rules" and body["ai_generated"] is False
    assert len(body["products"]) == 2
    labels = [row["label"] for row in body["rows"]]
    assert {"Price", "Brand", "Rating", "Availability", "Battery"} <= set(labels)
    assert body["highlights"]["cheapest"] == ids[0]
    assert body["summary"]["text"]
    assert any(row["differs"] for row in body["rows"])


def test_compare_validation(app, client):
    one = _ids(app, "HP-001")
    assert client.post("/api/compare", json={"product_ids": one}).status_code == 400
    assert client.post("/api/compare", json={"product_ids": one * 2}).status_code == 400
    assert client.post("/api/compare", json={"product_ids": [1, 99999]}).status_code == 404
    assert client.post("/api/compare", json={"product_ids": "1,2"}).status_code == 400
    assert client.post("/api/compare", json={"product_ids": [1, 2, 3, 4, 5]}).status_code == 400


def test_compare_with_gemini(app, client, configured_gemini, monkeypatch):
    ids = _ids(app, "HP-001", "HP-002")
    payload = {"summary": "QuietWave adds noise cancellation while BassBuds costs less.",
               "best_value": {"product_id": ids[1], "why": "ANC for a modest premium"},
               "key_differences": ["ANC vs none"], "value_for_money": []}
    monkeypatch.setattr(gemini_service, "_call_model", lambda p, json_mode: json.dumps(payload))
    body = client.post("/api/compare", json={"product_ids": ids}).get_json()
    assert body["source"] == "gemini" and body["summary"]["best_value"]["product_id"] == ids[1]


# ---- Reviews -------------------------------------------------------------- #
def test_review_analysis_from_database(app, client):
    pid = _ids(app, "SM-001")[0]
    body = client.post("/api/reviews/analyze", json={"product_id": pid}).get_json()
    assert body["reviews_analyzed"] == 3
    assert body["reliable"] is False and "too small" in body["reliability_note"]
    assert body["source"] == "rules" and body["ai_generated"] is False
    assert body["is_sample_data"] is True
    assert body["positives"]


def test_review_analysis_from_user_text(client):
    text = "Battery is great and lasts long.\n\nThe screen is dim and the price is too high.\n\n" \
           "Camera is excellent. Battery is amazing.\n\nBuild feels cheap and weak.\n\nGreat sound."
    body = client.post("/api/reviews/analyze", json={"text": text}).get_json()
    assert body["reviews_analyzed"] == 5 and body["reliable"] is True
    assert body["origin"] == "user_text"
    assert any("Battery" in p for p in body["positives"])


def test_review_analysis_list_and_validation(client):
    body = client.post("/api/reviews/analyze",
                       json={"reviews": ["Great battery", "Slow and warm"]}).get_json()
    assert body["reviews_analyzed"] == 2 and body["reliable"] is False
    assert client.post("/api/reviews/analyze", json={}).status_code == 400
    assert client.post("/api/reviews/analyze", json={"product_id": 99999}).status_code == 404
    assert client.post("/api/reviews/analyze", json={"text": "  "}).status_code == 400
    assert client.post("/api/reviews/analyze", json={"reviews": "x"}).status_code == 400
    assert client.post("/api/reviews/analyze", json={"text": "a" * 9000}).status_code == 400


def test_review_analysis_gemini(client, configured_gemini, monkeypatch):
    payload = {"summary": "Reviewers like the battery.", "positives": ["Battery"],
               "negatives": [], "common_complaints": []}
    monkeypatch.setattr(gemini_service, "_call_model", lambda p, json_mode: json.dumps(payload))
    body = client.post("/api/reviews/analyze", json={"reviews": ["Good battery"]}).get_json()
    assert body["source"] == "gemini" and body["reviews_analyzed"] == 1 and not body["reliable"]


# ---- Chat ----------------------------------------------------------------- #
def test_chat_fallback(client):
    r = client.post("/api/chat", json={"message": "Which headphones are good under 3000?"})
    body = r.get_json()
    assert r.status_code == 200
    assert body["source"] == "rules" and body["ai_generated"] is False
    assert "can't use the AI model" in body["reply"]
    assert body["product_ids"]


def test_chat_with_gemini_and_unsupported_price_guard(app, client, configured_gemini, monkeypatch):
    monkeypatch.setattr(gemini_service, "_call_model",
                        lambda p, json_mode: "The QuietWave ANC costs ₹2,799 (sample price).")
    body = client.post("/api/chat", json={"message": "tell me about headphones"}).get_json()
    assert body["source"] == "gemini"

    monkeypatch.setattr(gemini_service, "_call_model",
                        lambda p, json_mode: "It is only ₹1,234 right now!")
    body = client.post("/api/chat", json={"message": "tell me about headphones"}).get_json()
    assert body["source"] == "rules" and "1,234" not in body["reply"]


def test_chat_validation(client):
    assert client.post("/api/chat", json={}).status_code == 400
    assert client.post("/api/chat", json={"message": "x" * 1001}).status_code == 400
    assert client.post("/api/chat", json={"message": "hi", "history": "bad"}).status_code == 400
    assert client.post("/api/chat", json={"message": "hi",
                                          "history": [{"role": "system", "content": "x"}]}).status_code == 400


def test_api_key_never_exposed(app, client, configured_gemini):
    for path in ("/api/health", "/api/products", "/api/categories", "/api/cart"):
        assert "test-key" not in client.get(path).get_data(as_text=True)


def test_request_size_limit_and_unknown_route(client):
    r = client.post("/api/chat", data=json.dumps({"message": "x" * 200000}),
                    content_type="application/json")
    assert r.status_code == 413
    assert client.get("/api/nope").get_json()["error"]["code"] == "not_found"
