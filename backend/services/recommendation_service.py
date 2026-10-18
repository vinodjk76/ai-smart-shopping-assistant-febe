"""Deterministic query parsing, candidate retrieval, scoring and recommendations.

Used both to pick candidates that are sent to Gemini and as the fallback when
Gemini is unavailable. Everything here is derived only from database records.
"""
import re

from models import Product

STOPWORDS = {
    "a", "an", "the", "for", "and", "or", "with", "good", "best", "find", "me",
    "recommend", "show", "i", "need", "want", "to", "of", "in", "on", "my", "is",
    "are", "under", "below", "above", "over", "less", "than", "up", "within",
    "around", "about", "budget", "price", "compare", "cheap", "please", "some",
    "that", "has", "have", "which", "what", "how", "can", "you", "get", "buy",
    "rs", "inr", "at", "most", "max", "maximum", "from", "between",
}

# keyword (singular/plural/synonyms) -> category name in the DB
CATEGORY_KEYWORDS = {
    "smartphone": "Smartphones", "smartphones": "Smartphones", "phone": "Smartphones",
    "phones": "Smartphones", "mobile": "Smartphones", "mobiles": "Smartphones",
    "laptop": "Laptops", "laptops": "Laptops", "notebook": "Laptops",
    "headphone": "Headphones", "headphones": "Headphones", "earbuds": "Headphones",
    "earphones": "Headphones", "earbud": "Headphones", "headset": "Headphones",
    "appliance": "Home Appliances", "appliances": "Home Appliances",
    "ac": "Home Appliances", "vacuum": "Home Appliances", "mixer": "Home Appliances",
    "grinder": "Home Appliances", "accessory": "Accessories",
    "accessories": "Accessories", "charger": "Accessories", "keyboard": "Accessories",
    "mouse": "Accessories", "powerbank": "Accessories",
}

# phrase in the user's query -> terms to look for in features/specs/description
FEATURE_SYNONYMS = {
    "battery": ["battery"],
    "programming": ["programming", "coding", "16 gb", "32 gb"],
    "coding": ["programming", "coding", "16 gb", "32 gb"],
    "gaming": ["gpu", "gaming", "high refresh", "165 hz", "120 hz"],
    "camera": ["camera", "mp"],
    "noise": ["noise cancellation", "anc"],
    "anc": ["noise cancellation", "anc"],
    "bass": ["bass"],
    "fast": ["fast charging", "fast"],
    "charging": ["charging"],
    "lightweight": ["lightweight", "light"],
    "travel": ["lightweight", "compact", "foldable", "travel"],
    "student": ["student", "budget friendly"],
    "5g": ["5g"],
    "energy": ["energy efficient", "star"],
}

_NUM = r"(\d[\d,]*(?:\.\d+)?)\s*(k|thousand|lakh|lakhs|l)?"
_CUR = r"(?:₹|rs\.?|inr)?\s*"
_MAX_RE = re.compile(
    r"(?:under|below|less than|upto|up to|within|max(?:imum)?|at most|<=?)\s*" + _CUR + _NUM,
    re.I,
)
_MIN_RE = re.compile(r"(?:above|over|more than|at least|min(?:imum)?|>=?)\s*" + _CUR + _NUM, re.I)
_AROUND_RE = re.compile(r"(?:around|about|approximately|approx\.?)\s*" + _CUR + _NUM, re.I)
_BARE_RE = re.compile(r"(?:₹|rs\.?|inr)\s*" + _NUM, re.I)


def _to_amount(number: str, suffix: str | None) -> float:
    value = float(number.replace(",", ""))
    suffix = (suffix or "").lower()
    if suffix in ("k", "thousand"):
        value *= 1_000
    elif suffix in ("l", "lakh", "lakhs"):
        value *= 100_000
    return value


def parse_query(text: str) -> dict:
    """Extract budget, category and keywords from a natural-language query."""
    text = (text or "").strip()
    lowered = text.lower()
    max_price = min_price = None

    m = _MAX_RE.search(text)
    if m:
        max_price = _to_amount(m.group(1), m.group(2))
    m = _MIN_RE.search(text)
    if m:
        min_price = _to_amount(m.group(1), m.group(2))
    m = _AROUND_RE.search(text)
    if m and max_price is None and min_price is None:
        centre = _to_amount(m.group(1), m.group(2))
        min_price, max_price = centre * 0.8, centre * 1.2
    if max_price is None and min_price is None:
        m = _BARE_RE.search(text)
        if m:
            max_price = _to_amount(m.group(1), m.group(2))

    # Remove budget expressions so numbers/suffixes ("15k", "lakh") are not keywords.
    stripped = text
    for pattern in (_MAX_RE, _MIN_RE, _AROUND_RE, _BARE_RE):
        stripped = pattern.sub(" ", stripped)
    words = re.findall(r"[a-z0-9\+]+", lowered)
    categories = []
    for w in words:
        cat = CATEGORY_KEYWORDS.get(w)
        if cat and cat not in categories:
            categories.append(cat)

    keywords = [w for w in re.findall(r"[a-z0-9\+]+", stripped.lower())
                if w not in STOPWORDS and not w.isdigit() and len(w) > 1]
    return {
        "max_price": max_price,
        "min_price": min_price,
        "categories": categories,
        "keywords": keywords,
        "wants_comparison": "compare" in words or "versus" in words or "vs" in words,
    }


def _haystack(product: Product) -> str:
    specs = " ".join(f"{k} {v}" for k, v in (product.specs or {}).items())
    feats = " ".join(product.features or [])
    return " ".join(
        [product.name, product.brand, product.category, product.description or "", feats, specs]
    ).lower()


def _matched_features(product: Product, keywords: list[str]) -> list[str]:
    hay = _haystack(product)
    matched = []
    for kw in keywords:
        terms = FEATURE_SYNONYMS.get(kw, [kw])
        if any(t in hay for t in terms):
            matched.append(kw)
    return matched


def score_product(product: Product, parsed: dict) -> dict:
    """Deterministic score (0-100-ish) plus the facts that drove it."""
    price = product.best_price()
    amount = float(price.amount) if price else None
    score = (product.rating or 0) * 10  # up to 50
    reasons, limitations = [], []
    strengths = []

    cats = parsed["categories"]
    if cats:
        if product.category in cats:
            score += 20
            reasons.append(f"In the {product.category} category you asked about")
        else:
            score -= 40

    matched = _matched_features(product, parsed["keywords"])
    score += 8 * len(matched)
    for kw in matched:
        strengths.append(f"Matches '{kw}' in its listed features/specs")

    budget_fit = "no budget given"
    max_price, min_price = parsed["max_price"], parsed["min_price"]
    if amount is None:
        budget_fit = "price unavailable"
        limitations.append("No price data is stored for this product")
    else:
        if max_price is not None:
            if amount <= max_price:
                headroom = (max_price - amount) / max_price if max_price else 0
                score += 15 + 10 * headroom
                budget_fit = f"within budget (₹{amount:,.0f} ≤ ₹{max_price:,.0f})"
                reasons.append("Fits your budget")
            else:
                score -= 60
                budget_fit = f"over budget (₹{amount:,.0f} > ₹{max_price:,.0f})"
                limitations.append("Priced above your stated budget")
        if min_price is not None and amount < min_price:
            score -= 20
            limitations.append("Priced below your stated minimum")

    if (product.rating or 0) >= 4.3:
        strengths.append(f"High sample rating ({product.rating}/5)")
    elif (product.rating or 0) and product.rating < 4.0:
        limitations.append(f"Lower sample rating ({product.rating}/5)")
    if not product.in_stock:
        score -= 15
        limitations.append("Marked out of stock in the sample data")
    if product.is_sample:
        limitations.append("Based on demo/sample data, not verified market info")

    return {
        "score": round(score, 2),
        "matched_keywords": matched,
        "reasons": reasons,
        "strengths": strengths,
        "limitations": limitations,
        "budget_fit": budget_fit,
    }


def get_candidates(parsed: dict, limit: int = 8) -> list[tuple[Product, dict]]:
    """Retrieve products from the DB, score them and return the best `limit`."""
    query = Product.query
    if parsed["categories"]:
        query = query.filter(Product.category.in_(parsed["categories"]))
    products = query.all()
    scored = [(p, score_product(p, parsed)) for p in products]
    scored.sort(key=lambda pair: (-pair[1]["score"], pair[0].id))
    return scored[:limit]


def fallback_recommendations(query: str, limit: int = 5) -> dict:
    """Rule-based recommendations — never presented as AI generated."""
    parsed = parse_query(query)
    candidates = get_candidates(parsed, limit=limit * 2)
    # Prefer products that satisfy hard budget constraints when any exist.
    in_budget = [c for c in candidates if not c[1]["budget_fit"].startswith("over")]
    chosen = (in_budget or candidates)[:limit]
    items = []
    for product, info in chosen:
        reasons = info["reasons"] or ["Highly rated among available products"]
        items.append({
            "product_id": product.id,
            "product": product.to_dict(),
            "reasons": reasons,
            "strengths": info["strengths"],
            "limitations": info["limitations"],
            "budget_fit": info["budget_fit"],
            "score": info["score"],
        })
    return {"parsed": _public_parsed(parsed), "items": items}


def _public_parsed(parsed: dict) -> dict:
    return {
        "max_price": parsed["max_price"],
        "min_price": parsed["min_price"],
        "categories": parsed["categories"],
        "keywords": parsed["keywords"],
    }


def product_context(product: Product) -> dict:
    """Compact, factual record handed to Gemini (no personal data)."""
    best = product.best_price()
    return {
        "id": product.id,
        "name": product.name,
        "brand": product.brand,
        "category": product.category,
        "price_inr": float(best.amount) if best else None,
        "price_is_sample": bool(best.is_sample) if best else None,
        "rating": product.rating,
        "rating_count": product.rating_count,
        "in_stock": product.in_stock,
        "features": product.features or [],
        "specs": product.specs or {},
        "description": product.description or "",
    }
