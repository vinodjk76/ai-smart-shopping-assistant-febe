import { Link } from "react-router-dom";
import { useShop } from "../hooks/useShop.jsx";

/**
 * Side-by-side table. Rows whose values differ are highlighted; the cheapest,
 * highest-rated and best-value products get badges in the header.
 */
export default function ComparisonTable({ products, rows, highlights = {} }) {
  const { toggleCompare, addToCart } = useShop();

  const badges = (id) => {
    const b = [];
    if (highlights.cheapest === id) b.push("Lowest price");
    if (highlights.highest_rated === id) b.push("Top rated");
    if (highlights.best_value === id) b.push("Best value*");
    return b;
  };

  return (
    <div className="table-wrap" tabIndex={0} role="region" aria-label="Product comparison table">
      <table className="compare-table">
        <thead>
          <tr>
            <th scope="col">Feature</th>
            {products.map((p) => (
              <th scope="col" key={p.id}>
                <Link to={`/products/${p.id}`}>{p.name}</Link>
                <div className="badge-row">
                  {badges(p.id).map((b) => (
                    <span key={b} className="badge badge-ai">{b}</span>
                  ))}
                </div>
                <div className="row gap-sm">
                  <button className="btn btn-sm btn-primary" disabled={!p.in_stock}
                          onClick={() => addToCart(p.id, 1)}>Add to cart</button>
                  <button className="btn btn-sm btn-ghost" onClick={() => toggleCompare(p.id)}
                          aria-label={`Remove ${p.name} from comparison`}>Remove</button>
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label} className={row.differs ? "differs" : ""}>
              <th scope="row">
                {row.label}
                {row.differs ? <span className="sr-only"> (differs between products)</span> : null}
              </th>
              {row.values.map((v, i) => (
                <td key={i}>{v}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="muted small">
        Highlighted rows differ between the selected products. *Best value is a simple heuristic
        (rating points per rupee using sample data), not a guarantee.
      </p>
    </div>
  );
}
