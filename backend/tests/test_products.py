from models import Product
from seed import seed
from services.recommendation_service import parse_query


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "ok"
    assert body["products"] > 0
    assert body["gemini_configured"] is False
    assert "key" not in str(body).lower().replace("gemini_configured", "")


def test_seed_is_idempotent(app):
    before = Product.query.count()
    assert seed() == 0
    assert Product.query.count() == before


def test_list_and_sample_labels(client):
    r = client.get("/api/products")
    body = r.get_json()
    assert r.status_code == 200 and body["total"] >= 10
    assert all(p["is_sample"] and p["data_label"] == "Demo/sample data" for p in body["items"])
    assert all(p["price_verified"] is False for p in body["items"])


def test_category_and_price_filters(client):
    r = client.get("/api/products?category=Headphones&max_price=3000")
    items = r.get_json()["items"]
    assert items and all(p["category"] == "Headphones" and p["price"] <= 3000 for p in items)


def test_brand_rating_filters(client):
    items = client.get("/api/products?brand=Sonara&min_rating=4.2").get_json()["items"]
    assert items and all(p["brand"] == "Sonara" and p["rating"] >= 4.2 for p in items)


def test_sorting(client):
    asc = [p["price"] for p in client.get("/api/products?sort=price_asc&per_page=50").get_json()["items"]]
    desc = [p["price"] for p in client.get("/api/products?sort=price_desc&per_page=50").get_json()["items"]]
    assert asc == sorted(asc) and desc == sorted(desc, reverse=True)
    names = [p["name"].lower() for p in client.get("/api/products?sort=name&per_page=50").get_json()["items"]]
    assert names == sorted(names)
    ratings = [p["rating"] for p in client.get("/api/products?sort=rating&per_page=50").get_json()["items"]]
    assert ratings == sorted(ratings, reverse=True)


def test_natural_language_query(client):
    body = client.get("/api/products?q=Find the best headphones under ₹3,000").get_json()
    assert body["interpreted_query"]["max_price"] == 3000
    assert body["items"] and all(p["category"] == "Headphones" and p["price"] <= 3000
                                 for p in body["items"])


def test_parse_query_budgets():
    assert parse_query("laptop for programming under ₹60,000")["max_price"] == 60000
    assert parse_query("phone below 15k")["max_price"] == 15000
    assert parse_query("laptop under 1 lakh")["max_price"] == 100000
    assert parse_query("laptop for programming under ₹60,000")["categories"] == ["Laptops"]


def test_keyword_search_by_brand(client):
    items = client.get("/api/products?q=sonara").get_json()["items"]
    assert items and all(p["brand"] == "Sonara" for p in items)


def test_invalid_params(client):
    assert client.get("/api/products?max_price=abc").status_code == 400
    assert client.get("/api/products?sort=bogus").status_code == 400
    assert client.get("/api/products?min_price=500&max_price=100").status_code == 400
    r = client.get("/api/products?per_page=1000")
    assert r.status_code == 400
    assert r.get_json()["error"]["code"] == "validation_error"


def test_product_detail_and_price_comparison(client):
    pid = client.get("/api/products").get_json()["items"][0]["id"]
    r = client.get(f"/api/products/{pid}")
    body = r.get_json()
    assert r.status_code == 200
    assert body["specs"] and body["prices"]
    pc = body["price_comparison"]
    assert pc["has_verified_prices"] is False
    assert "No live retailer API" in pc["note"]
    assert all(p["is_sample"] for p in pc["prices"])
    assert body["source_url"] is None  # never fabricate product links


def test_product_not_found(client):
    r = client.get("/api/products/99999")
    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "not_found"


def test_categories(client):
    body = client.get("/api/categories").get_json()
    names = {c["name"] for c in body["categories"]}
    assert {"Smartphones", "Laptops", "Headphones", "Home Appliances", "Accessories"} <= names
    assert body["brands"]
