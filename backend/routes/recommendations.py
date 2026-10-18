"""AI (Gemini) and rule-based product recommendations."""
import logging

from flask import Blueprint, current_app, jsonify

from api_utils import get_json_body, require_int, require_text
from extensions import db
from models import Product
from services import gemini_service
from services.gemini_service import GeminiError
from services.recommendation_service import (
    fallback_recommendations,
    get_candidates,
    parse_query,
    product_context,
    _public_parsed,
)

bp = Blueprint("recommendations", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)


@bp.post("/recommendations")
def recommendations():
    body = get_json_body()
    query = require_text(body.get("query"), "query", current_app.config["MAX_QUERY_LENGTH"])
    limit = require_int(body.get("limit", 5), "limit", minimum=1, maximum=10)

    parsed = parse_query(query)
    candidates = get_candidates(parsed, limit=8)
    if not candidates:
        return jsonify({
            "source": "rules", "ai_generated": False, "fallback_reason": None,
            "parsed": _public_parsed(parsed), "items": [],
            "notice": "No products are available to recommend.",
        })

    reason = "ai_error"
    if gemini_service.is_configured():
        contexts = [product_context(p) for p, _ in candidates]
        info_by_id = {p.id: info for p, info in candidates}
        try:
            ai_items = gemini_service.recommend(query, contexts, limit=limit)
            items = []
            for ai in ai_items:
                product = db.session.get(Product, ai["product_id"])
                if product is None:  # defensive: IDs were already validated
                    continue
                det = info_by_id[product.id]
                items.append({
                    "product_id": product.id,
                    "product": product.to_dict(),  # facts always come from the DB
                    "reasons": [ai["reason"]] if ai["reason"] else det["reasons"],
                    "strengths": ai["strengths"] or det["strengths"],
                    "limitations": ai["limitations"] or det["limitations"],
                    # budget fit is computed from real prices, not by the model
                    "budget_fit": det["budget_fit"],
                })
            if items:
                return jsonify({
                    "source": "gemini", "ai_generated": True, "fallback_reason": None,
                    "parsed": _public_parsed(parsed), "items": items,
                    "notice": "Ranked and explained by Gemini using database product data. "
                              "Prices are sample data.",
                })
        except GeminiError as exc:
            logger.warning("Recommendation fallback: %s", exc)
            reason = "ai_error"
    else:
        reason = "ai_not_configured"

    result = fallback_recommendations(query, limit=limit)
    result.update({
        "source": "rules", "ai_generated": False, "fallback_reason": reason,
        "notice": "AI is unavailable, so these results come from a rule-based "
                  "algorithm (budget, category, rating and feature matching), not Gemini.",
    })
    return jsonify(result)
