import { Link } from "react-router-dom";
import ProductImage from "./ProductImage.jsx";
import DataBadge from "./DataBadge.jsx";
import { useShop } from "../hooks/useShop.jsx";
import { formatPrice } from "../utils/format";

export function Stars({ rating, count }) {
  const full = Math.round(rating || 0);
  return (
    <span className="stars" aria-label={`Rated ${rating} out of 5`}>
      <span aria-hidden="true">{"★".repeat(full)}{"☆".repeat(5 - full)}</span>{" "}
      <span className="muted">{rating?.toFixed(1)}{count ? ` (${count.toLocaleString("en-IN")})` : ""}</span>
    </span>
  );
}

export default function ProductCard({ product, footer }) {
  const { addToCart, toggleWishlist, isWishlisted, toggleCompare, inCompare } = useShop();
  const wished = isWishlisted(product.id);
  const comparing = inCompare(product.id);

  return (
    <article className="card product-card">
      <button
        className={`wish-btn ${wished ? "on" : ""}`}
        aria-pressed={wished}
        aria-label={wished ? `Remove ${product.name} from wishlist` : `Add ${product.name} to wishlist`}
        onClick={() => toggleWishlist(product.id)}
      >
        {wished ? "♥" : "♡"}
      </button>

      <Link to={`/products/${product.id}`} className="card-link" aria-label={`View ${product.name}`}>
        <ProductImage product={product} />
      </Link>

      <div className="card-body">
        <div className="muted small">{product.brand} · {product.category}</div>
        <h3 className="card-title">
          <Link to={`/products/${product.id}`}>{product.name}</Link>
        </h3>
        <Stars rating={product.rating} count={product.rating_count} />
        <div className="price-row">
          <strong className="price">{formatPrice(product.price, product.currency)}</strong>
          <DataBadge isSample={product.is_sample} verified={product.price_verified} label={product.is_sample ? "Sample price" : undefined} />
        </div>
        <div className={`availability ${product.in_stock ? "in" : "out"}`}>
          {product.in_stock ? "● In stock" : "● Out of stock"}
          {product.is_sample ? " (sample)" : ""}
        </div>
        {footer}
      </div>

      <div className="card-actions">
        <button
          className="btn btn-primary btn-sm"
          disabled={!product.in_stock || product.price === null}
          onClick={() => addToCart(product.id, 1)}
        >
          Add to cart
        </button>
        <button
          className={`btn btn-sm ${comparing ? "btn-active" : "btn-ghost"}`}
          aria-pressed={comparing}
          onClick={() => toggleCompare(product.id)}
        >
          {comparing ? "✓ Comparing" : "Compare"}
        </button>
      </div>
    </article>
  );
}
