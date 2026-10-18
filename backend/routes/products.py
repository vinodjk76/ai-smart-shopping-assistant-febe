"""Product search, filtering, sorting, details and categories."""
from flask import Blueprint, jsonify, request
from sqlalchemy import func

from api_utils import ApiError, query_float, query_int
from extensions import db
from models import Product, ProductPrice
from services.price_service import get_price_comparison
from services.recommendation_service import FEATURE_SYNONYMS, parse_query

bp = Blueprint("products", __name__, url_prefix="/api")

SORTS = {"relevance", "price_asc", "price_desc", "rating", "name"}


def _price_subquery():
    return (
        db.session.query(
            ProductPrice.product_id.label("product_id"),
            func.min(ProductPrice.amount).label("min_price"),
        )
        .group_by(ProductPrice.product_id)
        .subquery()
    )


def _text_score(product: Product, keywords: list[str]) -> int:
    specs = " ".join(f"{k} {v}" for k, v in (product.specs or {}).items())
    hay = " ".join([
        product.name, product.brand, product.category, product.description or "",
        " ".join(product.features or []), specs,
    ]).lower()
    score = 0
    for kw in keywords:
        terms = FEATURE_SYNONYMS.get(kw, [kw])
        if kw in hay or any(t in hay for t in terms):
            score += 1
    return score


@bp.get("/products")
def list_products():
    q = (request.args.get("q") or "").strip()
    if len(q) > 200:
        raise ApiError("Query parameter 'q' must be at most 200 characters", 400,
                       "validation_error")
    category = (request.args.get("category") or "").strip()
    brand = (request.args.get("brand") or "").strip()
    min_price = query_float("min_price", minimum=0)
    max_price = query_float("max_price", minimum=0)
    min_rating = query_float("min_rating", minimum=0, maximum=5)
    in_stock = request.args.get("in_stock")
    sort = request.args.get("sort") or ("relevance" if q else "rating")
    if sort not in SORTS:
        raise ApiError(f"'sort' must be one of {sorted(SORTS)}", 400, "validation_error")
    page = query_int("page", 1, minimum=1)
    per_page = query_int("per_page", 12, minimum=1, maximum=50)
    if min_price is not None and max_price is not None and min_price > max_price:
        raise ApiError("'min_price' cannot be greater than 'max_price'", 400,
                       "validation_error")

    # Natural-language interpretation; explicit filters always win.
    parsed = parse_query(q) if q else None
    interpreted = {}
    keywords = []
    if parsed:
        if max_price is None and parsed["max_price"] is not None:
            max_price = parsed["max_price"]
            interpreted["max_price"] = max_price
        if min_price is None and parsed["min_price"] is not None:
            min_price = parsed["min_price"]
            interpreted["min_price"] = min_price
        keywords = [k for k in parsed["keywords"]
                    if k not in {"compare", "versus", "vs"}]
        # words that named a category are consumed by the category filter
        from services.recommendation_service import CATEGORY_KEYWORDS
        keywords = [k for k in keywords if k not in CATEGORY_KEYWORDS]

    price_sq = _price_subquery()
    query = db.session.query(Product).outerjoin(price_sq, price_sq.c.product_id == Product.id)

    if category:
        query = query.filter(func.lower(Product.category) == category.lower())
    elif parsed and parsed["categories"]:
        query = query.filter(Product.category.in_(parsed["categories"]))
        interpreted["categories"] = parsed["categories"]
    if brand:
        query = query.filter(func.lower(Product.brand) == brand.lower())
    if min_price is not None:
        query = query.filter(price_sq.c.min_price >= min_price)
    if max_price is not None:
        query = query.filter(price_sq.c.min_price <= max_price)
    if min_rating is not None:
        query = query.filter(Product.rating >= min_rating)
    if in_stock in ("1", "true", "True"):
        query = query.filter(Product.in_stock.is_(True))

    products = query.all()
    scores = {}
    if keywords:
        scores = {p.id: _text_score(p, keywords) for p in products}
        products = [p for p in products if scores[p.id] > 0]
        interpreted["keywords"] = keywords

    def price_of(p):
        best = p.best_price()
        return float(best.amount) if best else float("inf")

    if sort == "price_asc":
        products.sort(key=lambda p: (price_of(p), p.id))
    elif sort == "price_desc":
        products.sort(key=lambda p: (-price_of(p) if price_of(p) != float("inf") else 0, p.id))
    elif sort == "name":
        products.sort(key=lambda p: p.name.lower())
    elif sort == "rating" or not scores:
        products.sort(key=lambda p: (-(p.rating or 0), p.id))
    else:  # relevance
        products.sort(key=lambda p: (-scores.get(p.id, 0), -(p.rating or 0), p.id))

    total = len(products)
    start = (page - 1) * per_page
    items = [p.to_dict() for p in products[start:start + per_page]]
    return jsonify({
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "interpreted_query": interpreted,
        "data_notice": "Product data shown is demo/sample data unless an item says otherwise.",
    })


@bp.get("/products/<int:product_id>")
def get_product(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        raise ApiError("Product not found", 404, "not_found")
    data = product.to_dict(detail=True)
    data["price_comparison"] = get_price_comparison(product)
    return jsonify(data)


@bp.get("/categories")
def list_categories():
    rows = (
        db.session.query(Product.category, func.count(Product.id))
        .group_by(Product.category)
        .order_by(Product.category)
        .all()
    )
    brands = [b for (b,) in db.session.query(Product.brand).distinct().order_by(Product.brand)]
    return jsonify({
        "categories": [{"name": name, "count": count} for name, count in rows],
        "brands": brands,
    })
