"""Review analysis (Gemini with a deterministic lexicon-based fallback)."""
import logging
import re

from flask import Blueprint, current_app, jsonify

from api_utils import ApiError, get_json_body, require_int, require_text
from extensions import db
from models import Product
from services import gemini_service
from services.gemini_service import GeminiError

bp = Blueprint("reviews", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

MIN_RELIABLE_REVIEWS = 5
MAX_REVIEWS = 50

THEMES = {
    "Battery": ["battery", "charging", "charge"],
    "Camera": ["camera", "photo", "photos"],
    "Sound": ["sound", "bass", "treble", "speakers", "audio", "mic"],
    "Price / value": ["price", "value", "pricey", "expensive", "cheap", "worth"],
    "Comfort": ["comfortable", "comfort", "fit", "light", "heavy"],
    "Performance": ["fast", "slow", "lag", "performance", "smooth", "heats", "warm"],
    "Build": ["build", "sturdy", "durable", "solid"],
    "Display": ["screen", "display", "bright"],
    "Noise": ["noise", "noisy", "loud", "quiet", "fans"],
}
POSITIVE = {"great", "good", "excellent", "amazing", "perfect", "love", "best", "fast",
            "smooth", "comfortable", "sturdy", "solid", "easy", "quick", "impressive",
            "superb", "quiet", "durable", "reliable", "outstanding", "light", "compact"}
NEGATIVE = {"bad", "poor", "slow", "weak", "average", "expensive", "pricey", "heavy",
            "noisy", "loud", "warm", "hot", "drains", "stuck", "struggles", "muffled",
            "harsh", "delay", "issue", "problem", "disappointing", "basic", "sharp"}
NEGATIVE_PHRASES = ["not good", "not great", "no good", "so-so", "gets warm", "too long",
                    "takes a long time"]


def _split_text(text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()]
    return parts


def fallback_analysis(reviews: list[str], ratings: list[int] | None = None) -> dict:
    n = len(reviews)
    pos_counts, neg_counts = {}, {}
    for review in reviews:
        low = review.lower()
        sentences = [s for s in re.split(r"[.!?;]+", low) if s.strip()]
        for sentence in sentences:
            words = set(re.findall(r"[a-z\-]+", sentence))
            neg = bool(words & NEGATIVE) or any(ph in sentence for ph in NEGATIVE_PHRASES)
            pos = bool(words & POSITIVE) and not neg
            for theme, terms in THEMES.items():
                if words & set(terms):
                    if neg:
                        neg_counts[theme] = neg_counts.get(theme, 0) + 1
                    elif pos:
                        pos_counts[theme] = pos_counts.get(theme, 0) + 1

    def fmt(counts, sentiment):
        ordered = sorted(counts.items(), key=lambda kv: -kv[1])
        return [f"{t}: mentioned {sentiment} in {c} of {n} review(s)" for t, c in ordered[:5]]

    positives = fmt(pos_counts, "positively")
    negatives = fmt(neg_counts, "negatively")
    complaints = [f"{t} ({c} mention{'s' if c > 1 else ''})"
                  for t, c in sorted(neg_counts.items(), key=lambda kv: -kv[1]) if c > 1]
    parts = [f"Based on {n} review(s)."]
    if ratings:
        parts.append(f"Average review rating: {sum(ratings) / len(ratings):.1f}/5.")
    if positives:
        parts.append(f"Most positive theme: {positives[0].split(':')[0]}.")
    if negatives:
        parts.append(f"Most criticised theme: {negatives[0].split(':')[0]}.")
    return {
        "summary": " ".join(parts),
        "positives": positives,
        "negatives": negatives,
        "common_complaints": complaints,
    }


@bp.post("/reviews/analyze")
def analyze():
    body = get_json_body()
    max_len = current_app.config["MAX_REVIEW_TEXT_LENGTH"]
    reviews, ratings, origin, product_name = [], None, None, None

    if body.get("product_id") is not None:
        pid = require_int(body["product_id"], "product_id", minimum=1)
        product = db.session.get(Product, pid)
        if product is None:
            raise ApiError("Product not found", 404, "not_found")
        product_name = product.name
        origin = "database"
        reviews = [f"{r.title}. {r.body}".strip(". ") for r in product.reviews][:MAX_REVIEWS]
        ratings = [r.rating for r in product.reviews][:MAX_REVIEWS]
    elif body.get("reviews") is not None:
        raw = body["reviews"]
        if not isinstance(raw, list) or len(raw) > MAX_REVIEWS:
            raise ApiError(f"'reviews' must be a list of at most {MAX_REVIEWS} strings",
                           400, "validation_error")
        reviews = [require_text(r, "reviews[]", 2000) for r in raw]
        origin = "user_text"
    elif body.get("text") is not None:
        text = require_text(body["text"], "text", max_len)
        reviews = _split_text(text)[:MAX_REVIEWS]
        origin = "user_text"
    else:
        raise ApiError("Provide 'product_id', 'reviews' (list) or 'text'", 400,
                       "validation_error")

    if not reviews:
        raise ApiError("No reviews to analyze", 400, "validation_error")

    n = len(reviews)
    analysis, source, reason = None, "rules", None
    if gemini_service.is_configured():
        try:
            analysis = gemini_service.summarize_reviews(reviews)
            source = "gemini"
        except GeminiError as exc:
            logger.warning("Review analysis fallback: %s", exc)
            reason = "ai_error"
    else:
        reason = "ai_not_configured"
    if analysis is None:
        analysis = fallback_analysis(reviews, ratings)

    reliable = n >= MIN_RELIABLE_REVIEWS
    return jsonify({
        **analysis,
        "reviews_analyzed": n,
        "reliable": reliable,
        "reliability_note": (
            f"{n} review(s) analyzed."
            if reliable else
            f"Only {n} review(s) were available. This is too small a sample for a "
            f"reliable conclusion (at least {MIN_RELIABLE_REVIEWS} recommended)."
        ),
        "origin": origin,
        "product_name": product_name,
        "is_sample_data": origin == "database",
        "source": source,
        "ai_generated": source == "gemini",
        "fallback_reason": reason,
    })
