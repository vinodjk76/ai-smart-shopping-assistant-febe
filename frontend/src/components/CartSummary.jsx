import { Link } from "react-router-dom";
import { useShop } from "../hooks/useShop.jsx";
import { formatPrice } from "../utils/format";
import { EmptyState } from "./StateViews.jsx";
import ProductImage from "./ProductImage.jsx";

export default function CartSummary() {
  const { cart, updateQuantity, removeFromCart } = useShop();

  if (!cart.items.length) {
    return (
      <EmptyState
        icon="🛒"
        title="Your cart is empty"
        message="Add a few products to see them here."
        action={<Link to="/search" className="btn btn-primary">Browse products</Link>}
      />
    );
  }

  return (
    <div className="cart-layout">
      <ul className="cart-list" aria-label="Cart items">
        {cart.items.map((item) => (
          <li key={item.id} className="card cart-item">
            <ProductImage product={item.product} size="thumb" />
            <div className="cart-info">
              <Link to={`/products/${item.product_id}`}><strong>{item.product.name}</strong></Link>
              <div className="muted small">
                Unit price {formatPrice(item.unit_price, cart.currency)}
                {item.price_is_sample ? " (sample price)" : ""}
              </div>
              <div className="qty" role="group" aria-label={`Quantity for ${item.product.name}`}>
                <button className="btn btn-sm btn-ghost" disabled={item.quantity <= 1}
                        aria-label="Decrease quantity"
                        onClick={() => updateQuantity(item.id, item.quantity - 1)}>−</button>
                <span aria-live="polite" className="qty-value">{item.quantity}</span>
                <button className="btn btn-sm btn-ghost" disabled={item.quantity >= 10}
                        aria-label="Increase quantity"
                        onClick={() => updateQuantity(item.id, item.quantity + 1)}>+</button>
              </div>
            </div>
            <div className="cart-line">
              <strong>{formatPrice(item.line_total, cart.currency)}</strong>
              <button className="btn btn-sm btn-danger" onClick={() => removeFromCart(item.id)}
                      aria-label={`Remove ${item.product.name} from cart`}>Remove</button>
            </div>
          </li>
        ))}
      </ul>

      <aside className="card summary" aria-label="Order summary">
        <h2 className="h3">Summary</h2>
        <div className="summary-row"><span>Items</span><span>{cart.item_count}</span></div>
        <div className="summary-row total">
          <span>Total</span><span>{formatPrice(cart.total, cart.currency)}</span>
        </div>
        <p className="muted small">{cart.notice}</p>
        <button className="btn btn-primary" disabled title="Payments are not implemented in this demo">
          Checkout (demo disabled)
        </button>
      </aside>
    </div>
  );
}
