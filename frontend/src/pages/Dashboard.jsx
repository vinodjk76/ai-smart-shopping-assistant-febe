import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import SearchBar from "../components/SearchBar.jsx";
import ProductGrid from "../components/ProductGrid.jsx";
import { ErrorState } from "../components/StateViews.jsx";
import { CATEGORY_COLORS, CATEGORY_EMOJI, NATURAL_EXAMPLES } from "../utils/format";

const BUDGETS = [
  { label: "Under ₹3,000", max: 3000 },
  { label: "Under ₹20,000", max: 20000 },
  { label: "Under ₹60,000", max: 60000 },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const { data, loading, error, reload } = useAsync(async () => {
    const [featured, categories, ...budgets] = await Promise.all([
      api.products({ sort: "rating", per_page: 4 }),
      api.categories(),
      ...BUDGETS.map((b) => api.products({ max_price: b.max, sort: "rating", per_page: 4, in_stock: "true" })),
    ]);
    return { featured, categories, budgets };
  }, []);

  const goSearch = (q) => navigate(`/search?q=${encodeURIComponent(q)}`);

  return (
    <div className="stack">
      <section className="hero">
        <h1>Shop smarter with AI</h1>
        <p>Describe what you need and your budget. We search, compare and explain — using only real data from the catalogue.</p>
        <SearchBar onSearch={goSearch} />
        <div className="chips" aria-label="Example searches">
          {NATURAL_EXAMPLES.map((ex) => (
            <button key={ex} className="chip" onClick={() => goSearch(ex)}>{ex}</button>
          ))}
        </div>
      </section>

      {error ? <ErrorState message={error} onRetry={reload} /> : null}

      <section aria-labelledby="cats-h">
        <h2 id="cats-h">Shop by category</h2>
        <div className="cat-grid">
          {(data?.categories.categories || []).map((c) => {
            const [from, to] = CATEGORY_COLORS[c.name] || ["#64748b", "#334155"];
            return (
              <Link key={c.name} to={`/search?category=${encodeURIComponent(c.name)}`}
                    className="cat-tile" style={{ background: `linear-gradient(135deg, ${from}, ${to})` }}>
                <span className="cat-emoji" aria-hidden="true">{CATEGORY_EMOJI[c.name] || "🛍️"}</span>
                <strong>{c.name}</strong>
                <span className="small">{c.count} products</span>
              </Link>
            );
          })}
        </div>
      </section>

      <section aria-labelledby="feat-h">
        <div className="section-head">
          <h2 id="feat-h">Featured products</h2>
          <Link to="/search?sort=rating">View all →</Link>
        </div>
        <ProductGrid products={data?.featured.items} loading={loading} error={null} />
      </section>

      <section aria-labelledby="rec-h" className="callout">
        <div>
          <h2 id="rec-h">✨ Get AI recommendations</h2>
          <p className="muted">Tell us your needs and budget in plain English. Recommendations are ranked from the product database; prices are never invented.</p>
        </div>
        <Link to="/recommendations" className="btn btn-primary">Try AI picks</Link>
      </section>

      {BUDGETS.map((b, i) => (
        <section key={b.max} aria-labelledby={`budget-${i}`}>
          <div className="section-head">
            <h2 id={`budget-${i}`}>Budget picks: {b.label}</h2>
            <Link to={`/search?max_price=${b.max}&sort=rating`}>See more →</Link>
          </div>
          <ProductGrid
            products={data?.budgets[i]?.items}
            loading={loading}
            error={null}
            emptyTitle="Nothing in this budget"
            emptyMessage="No products match this price range."
          />
        </section>
      ))}
    </div>
  );
}
