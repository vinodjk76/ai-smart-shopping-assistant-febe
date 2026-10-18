"""SQLAlchemy models."""
from datetime import datetime, timezone

from sqlalchemy.orm import validates

from extensions import db


def utcnow():
    return datetime.now(timezone.utc)


def iso(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    brand = db.Column(db.String(100), nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, default="")
    specs = db.Column(db.JSON, default=dict)  # {"Battery": "5000 mAh", ...}
    features = db.Column(db.JSON, default=list)  # ["Noise cancellation", ...]
    image_url = db.Column(db.String(500), default="")
    source_url = db.Column(db.String(500), nullable=True)  # only if verified
    data_source = db.Column(db.String(100), default="demo_seed")
    is_sample = db.Column(db.Boolean, default=True, nullable=False)
    rating = db.Column(db.Float, default=0.0)  # sample rating for seeded data
    rating_count = db.Column(db.Integer, default=0)
    in_stock = db.Column(db.Boolean, default=True, nullable=False)
    stock_note = db.Column(db.String(200), default="Sample availability (demo data)")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    prices = db.relationship(
        "ProductPrice", backref="product", cascade="all, delete-orphan",
        order_by="ProductPrice.amount",
    )
    reviews = db.relationship(
        "Review", backref="product", cascade="all, delete-orphan"
    )

    @validates("rating")
    def _validate_rating(self, _key, value):
        value = float(value or 0)
        if not 0 <= value <= 5:
            raise ValueError("rating must be between 0 and 5")
        return value

    def best_price(self):
        """Lowest price among stored prices (None if there are none)."""
        if not self.prices:
            return None
        return min(self.prices, key=lambda p: p.amount)

    def to_dict(self, detail=False):
        best = self.best_price()
        data = {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "brand": self.brand,
            "category": self.category,
            "image_url": self.image_url,
            "rating": self.rating,
            "rating_count": self.rating_count,
            "in_stock": self.in_stock,
            "stock_note": self.stock_note,
            "price": float(best.amount) if best else None,
            "currency": best.currency if best else None,
            "price_source": best.source if best else None,
            "price_verified": best.is_verified if best else False,
            "is_sample": self.is_sample,
            "data_label": "Demo/sample data" if self.is_sample else "Source data",
            "source_url": self.source_url,
        }
        if detail:
            data.update(
                description=self.description,
                specs=self.specs or {},
                features=self.features or [],
                data_source=self.data_source,
                prices=[p.to_dict() for p in self.prices],
                review_count=len(self.reviews),
                updated_at=iso(self.updated_at),
            )
        return data


class ProductPrice(db.Model):
    __tablename__ = "product_prices"
    __table_args__ = (db.Index("ix_price_product_source", "product_id", "source"),)

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False, index=True
    )
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), default="INR", nullable=False)
    source = db.Column(db.String(100), nullable=False)
    source_url = db.Column(db.String(500), nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_sample = db.Column(db.Boolean, default=True, nullable=False)
    retrieved_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    @validates("amount")
    def _validate_amount(self, _key, value):
        if value is None or float(value) < 0:
            raise ValueError("price must be non-negative")
        return value

    def to_dict(self):
        return {
            "id": self.id,
            "amount": float(self.amount),
            "currency": self.currency,
            "source": self.source,
            "source_url": self.source_url,
            "is_verified": self.is_verified,
            "is_sample": self.is_sample,
            "label": "Sample price (demo data)" if self.is_sample else (
                "Verified price" if self.is_verified else "Unverified price"
            ),
            "retrieved_at": iso(self.retrieved_at),
        }


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False, index=True
    )
    author = db.Column(db.String(100), default="Anonymous")
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), default="")
    body = db.Column(db.Text, nullable=False)
    is_sample = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    @validates("rating")
    def _validate_rating(self, _key, value):
        value = int(value)
        if not 1 <= value <= 5:
            raise ValueError("review rating must be between 1 and 5")
        return value

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "author": self.author,
            "rating": self.rating,
            "title": self.title,
            "body": self.body,
            "is_sample": self.is_sample,
            "created_at": iso(self.created_at),
        }


class Cart(db.Model):
    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    items = db.relationship(
        "CartItem", backref="cart", cascade="all, delete-orphan",
        order_by="CartItem.id",
    )


class CartItem(db.Model):
    __tablename__ = "cart_items"
    __table_args__ = (
        db.UniqueConstraint("cart_id", "product_id", name="uq_cart_product"),
        db.CheckConstraint("quantity > 0", name="ck_cart_qty_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    product = db.relationship("Product")


class Wishlist(db.Model):
    __tablename__ = "wishlists"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    items = db.relationship(
        "WishlistItem", backref="wishlist", cascade="all, delete-orphan",
        order_by="WishlistItem.id",
    )


class WishlistItem(db.Model):
    __tablename__ = "wishlist_items"
    __table_args__ = (
        db.UniqueConstraint("wishlist_id", "product_id", name="uq_wishlist_product"),
    )

    id = db.Column(db.Integer, primary_key=True)
    wishlist_id = db.Column(
        db.Integer, db.ForeignKey("wishlists.id"), nullable=False, index=True
    )
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    added_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    product = db.relationship("Product")
