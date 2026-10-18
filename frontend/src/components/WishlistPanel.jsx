import { Link } from "react-router-dom";
import { useShop } from "../hooks/useShop.jsx";
import { formatPrice } from "../utils/format";
import { EmptyState } from "./StateViews.jsx";
import ProductImage from "./ProductImage.jsx";

export default function WishlistPanel() {
  const { wishlist, removeFromWishlist, addToCart } = useShop();

  if (!wishlist.items.length) {
    return (
      <EmptyState
        icon="♡"
        title="Your wishlist is empty"
        message="Tap the heart on any product to save it for later."
        action={<Link to="/search" className="btn btn-primary">Browse products</Link>}
      />
    );
  }

  return (
    <ul className="wishlist-list" aria-label="Wishlist items">
      {wishlist.items.map((item) => (
        <li key={item.id} className="card cart-item">
          <ProductImage product={item.product} size="thumb" />
          <div className="cart-info">
            <Link to={`/products/${item.product_id}`}><strong>{item.product.name}</strong></Link>
            <div className="muted small">{item.product.brand} · {item.product.category}</div>
            <div>
              {formatPrice(item.product.price, item.product.currency)}{" "}
              {item.product.is_sample ? <span className="badge badge-sample">Sample price</span> : null}
            </div>
          </div>
          <div className="cart-line">
            <button className="btn btn-sm btn-primary"
                    disabled={!item.product.in_stock || item.product.price === null}
                    onClick={() => addToCart(item.product_id, 1)}>Add to cart</button>
            <button className="btn btn-sm btn-ghost" onClick={() => removeFromWishlist(item.id)}
                    aria-label={`Remove ${item.product.name} from wishlist`}>Remove</button>
          </div>
        </li>
      ))}
    </ul>
  );
}
