"""Wishlist persisted in SQLite for the demo user."""
from flask import Blueprint, current_app, jsonify

from api_utils import ApiError, get_json_body, require_int
from extensions import db
from models import Product, Wishlist, WishlistItem, iso

bp = Blueprint("wishlist", __name__, url_prefix="/api")


def get_wishlist() -> Wishlist:
    user_id = current_app.config["DEMO_USER_ID"]
    wishlist = Wishlist.query.filter_by(user_id=user_id).first()
    if wishlist is None:
        wishlist = Wishlist(user_id=user_id)
        db.session.add(wishlist)
        db.session.commit()
    return wishlist


def serialize(wishlist: Wishlist) -> dict:
    return {
        "items": [
            {"id": i.id, "product_id": i.product_id, "product": i.product.to_dict(),
             "added_at": iso(i.added_at)}
            for i in wishlist.items
        ],
        "count": len(wishlist.items),
        "user": current_app.config["DEMO_USER_ID"],
    }


@bp.get("/wishlist")
def read_wishlist():
    return jsonify(serialize(get_wishlist()))


@bp.post("/wishlist/items")
def add_item():
    body = get_json_body()
    pid = require_int(body.get("product_id"), "product_id", minimum=1)
    if db.session.get(Product, pid) is None:
        raise ApiError("Product not found", 404, "not_found")
    wishlist = get_wishlist()
    existing = WishlistItem.query.filter_by(wishlist_id=wishlist.id, product_id=pid).first()
    status = 200  # idempotent: adding twice is not an error
    if existing is None:
        db.session.add(WishlistItem(wishlist_id=wishlist.id, product_id=pid))
        db.session.commit()
        status = 201
    return jsonify(serialize(wishlist)), status


@bp.delete("/wishlist/items/<int:item_id>")
def delete_item(item_id):
    wishlist = get_wishlist()
    item = WishlistItem.query.filter_by(id=item_id, wishlist_id=wishlist.id).first()
    if item is None:
        raise ApiError("Wishlist item not found", 404, "not_found")
    db.session.delete(item)
    db.session.commit()
    return jsonify(serialize(wishlist))
