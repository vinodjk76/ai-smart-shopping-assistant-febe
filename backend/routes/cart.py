"""Shopping cart. Prices and totals are always computed on the server from the DB."""
from decimal import Decimal

from flask import Blueprint, current_app, jsonify

from api_utils import ApiError, get_json_body, require_int
from extensions import db
from models import Cart, CartItem, Product

bp = Blueprint("cart", __name__, url_prefix="/api")


def get_cart() -> Cart:
    user_id = current_app.config["DEMO_USER_ID"]
    cart = Cart.query.filter_by(user_id=user_id).first()
    if cart is None:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()
    return cart


def serialize_cart(cart: Cart) -> dict:
    items, total = [], Decimal("0")
    currency = "INR"
    for item in cart.items:
        best = item.product.best_price()
        unit = Decimal(str(best.amount)) if best else Decimal("0")
        line = unit * item.quantity
        total += line
        items.append({
            "id": item.id,
            "product_id": item.product_id,
            "product": item.product.to_dict(),
            "quantity": item.quantity,
            "unit_price": float(unit),
            "line_total": float(line),
            "price_is_sample": bool(best.is_sample) if best else None,
        })
        if best:
            currency = best.currency
    return {
        "items": items,
        "item_count": sum(i["quantity"] for i in items),
        "total": float(total),
        "currency": currency,
        "notice": "Demo cart: prices are sample data and no payment is processed.",
        "user": current_app.config["DEMO_USER_ID"],
    }


@bp.get("/cart")
def read_cart():
    return jsonify(serialize_cart(get_cart()))


@bp.post("/cart/items")
def add_item():
    body = get_json_body()
    max_qty = current_app.config["MAX_CART_QUANTITY"]
    pid = require_int(body.get("product_id"), "product_id", minimum=1)
    qty = require_int(body.get("quantity", 1), "quantity", minimum=1, maximum=max_qty)
    product = db.session.get(Product, pid)
    if product is None:
        raise ApiError("Product not found", 404, "not_found")
    if product.best_price() is None:
        raise ApiError("This product has no price and cannot be added", 409, "no_price")
    if not product.in_stock:
        raise ApiError("This product is marked out of stock", 409, "out_of_stock")

    cart = get_cart()
    existing = CartItem.query.filter_by(cart_id=cart.id, product_id=pid).first()
    if existing:
        new_qty = existing.quantity + qty
        if new_qty > max_qty:
            raise ApiError(f"Maximum quantity per product is {max_qty}", 400,
                           "validation_error")
        existing.quantity = new_qty
    else:
        db.session.add(CartItem(cart_id=cart.id, product_id=pid, quantity=qty))
    db.session.commit()
    return jsonify(serialize_cart(cart)), 201


def _find_item(item_id: int) -> CartItem:
    cart = get_cart()
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if item is None:
        raise ApiError("Cart item not found", 404, "not_found")
    return item


@bp.patch("/cart/items/<int:item_id>")
def update_item(item_id):
    body = get_json_body()
    max_qty = current_app.config["MAX_CART_QUANTITY"]
    qty = require_int(body.get("quantity"), "quantity", minimum=1, maximum=max_qty)
    item = _find_item(item_id)
    item.quantity = qty
    db.session.commit()
    return jsonify(serialize_cart(get_cart()))


@bp.delete("/cart/items/<int:item_id>")
def delete_item(item_id):
    item = _find_item(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify(serialize_cart(get_cart()))
