"""Shopping chatbot (Gemini with a deterministic, clearly-labelled fallback)."""
import logging

from flask import Blueprint, current_app, jsonify

from api_utils import ApiError, get_json_body, require_text
from models import Product
from services import gemini_service
from services.gemini_service import GeminiError
from services.recommendation_service import get_candidates, parse_query, product_context

bp = Blueprint("chat", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)


def _clean_history(raw) -> list[dict]:
    if raw is None:
        return []
    if not isinstance(raw, list) or len(raw) > 30:
        raise ApiError("'history' must be a list of at most 30 messages", 400,
                       "validation_error")
    cleaned = []
    for m in raw[-6:]:
        if not isinstance(m, dict) or m.get("role") not in ("user", "assistant"):
            raise ApiError("Each history item needs role 'user' or 'assistant'", 400,
                           "validation_error")
        content = m.get("content")
        if not isinstance(content, str):
            raise ApiError("History 'content' must be a string", 400, "validation_error")
        cleaned.append({"role": m["role"], "content": content.strip()[:1000]})
    return cleaned


def fallback_reply(message: str, candidates) -> str:
    if not candidates:
        return "I don't have any product data to answer that yet."
    lines = ["I can't use the AI model right now, so here are the closest matches from "
             "the product database (sample data):"]
    for product, info in candidates[:3]:
        best = product.best_price()
        price = (f"₹{float(best.amount):,.0f} (sample price)" if best and best.is_sample
                 else (f"₹{float(best.amount):,.0f}" if best else "price unavailable"))
        lines.append(f"- {product.name} by {product.brand}: {price}, "
                     f"rated {product.rating}/5, {info['budget_fit']}.")
    return "\n".join(lines)


@bp.post("/chat")
def chat():
    body = get_json_body()
    message = require_text(body.get("message"), "message",
                           current_app.config["MAX_CHAT_LENGTH"])
    history = _clean_history(body.get("history"))

    # Use the latest message plus recent user turns to find relevant products.
    search_text = " ".join([m["content"] for m in history if m["role"] == "user"][-2:]
                           + [message])
    parsed = parse_query(search_text)
    candidates = get_candidates(parsed, limit=5)
    if not candidates:  # nothing matched the category: offer top-rated products
        top = Product.query.order_by(Product.rating.desc()).limit(5).all()
        candidates = [(p, {"budget_fit": "no budget given"}) for p in top]
    contexts = [product_context(p) for p, _ in candidates]

    source, reason, reply = "rules", None, None
    if gemini_service.is_configured():
        try:
            reply = gemini_service.chat(message, history, contexts)
            source = "gemini"
        except GeminiError as exc:
            logger.warning("Chat fallback: %s", exc)
            reason = "ai_error"
    else:
        reason = "ai_not_configured"
    if reply is None:
        reply = fallback_reply(message, candidates)

    return jsonify({
        "reply": reply,
        "source": source,
        "ai_generated": source == "gemini",
        "fallback_reason": reason,
        "product_ids": [p.id for p, _ in candidates],
    })
