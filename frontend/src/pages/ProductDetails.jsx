import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, errorMessage } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useShop } from "../hooks/useShop.jsx";
import ProductImage from "../components/ProductImage.jsx";
import DataBadge, { AiBadge } from "../components/DataBadge.jsx";
import { Stars } from "../components/ProductCard.jsx";
import { ErrorState, Spinner } from "../components/StateViews.jsx";
import { formatDate, formatPrice } from "../utils/format";
import { ReviewResult } from "./ReviewAnalyzerPage.jsx";

export default function ProductDetails() {
  const { id } = useParams();
  const { addToCart, toggleWishlist, isWishlisted, toggleCompare, inCompare } = useShop();
  const { data: p, loading, error, reload } = useAsync(() => api.product(id), [id]);
  const [qty, setQty] = useState(1);
  const [analysis, setAnalysis] = useState(null);
  const [analysisState, setAnalysisState] = useState({ loading: false, error: "" });

  if (loading) return <Spinner label="Loading product…" />;
  if (error) return <ErrorState message={error} onRetry={reload} />;

  const pc = p.price_comparison;
  const wished = isWishlisted(p.id);

  const runAnalysis = async () => {
    setAnalysisState({ loading: true, error: "" });
    try {
      setAnalysis(await api.analyzeReviews({ product_id: p.id }));
      setAnalysisState({ loading: false, error: "" });
    } catch (err) {
      setAnalysisState({ loading: false, error: errorMessage(err) });
    }
  };

  const askAi = () =>
    window.dispatchEvent(
      new CustomEvent("ask-ai", { detail: `Tell me about the ${p.name}: is it a good choice, and for whom?` })
    );

  return (
    <div className="stack">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to="/">Home</Link> / <Link to={`/search?category=${encodeURIComponent(p.category)}`}>{p.category}</Link> / {p.name}
      </nav>

      <div className="detail-grid">
        <ProductImage product={p} size="hero" />

        <div className="stack-sm">
          <div className="muted">{p.brand} · {p.category}</div>
          <h1>{p.name}</h1>
          <Stars rating={p.rating} count={p.rating_count} />
          <div className="price-row">
            <strong className="price big">{formatPrice(p.price, p.currency)}</strong>
            <DataBadge isSample={p.is_sample} verified={p.price_verified} label={p.is_sample ? "Sample price" : undefined} />
          </div>
          <div className={`availability ${p.in_stock ? "in" : "out"}`}>
            {p.in_stock ? "● In stock" : "● Out of stock"} <span className="muted">· {p.stock_note}</span>
          </div>
          <p>{p.description}</p>

          <div className="row wrap">
            <label className="qty-input">
              Qty
              <select value={qty} onChange={(e) => setQty(Number(e.target.value))}>
                {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </label>
            <button className="btn btn-primary" disabled={!p.in_stock || p.price === null}
                    onClick={() => addToCart(p.id, qty)}>Add to cart</button>
            <button className={`btn ${wished ? "btn-active" : "btn-ghost"}`} aria-pressed={wished}
                    onClick={() => toggleWishlist(p.id)}>{wished ? "♥ In wishlist" : "♡ Add to wishlist"}</button>
            <button className={`btn ${inCompare(p.id) ? "btn-active" : "btn-ghost"}`} aria-pressed={inCompare(p.id)}
                    onClick={() => toggleCompare(p.id)}>{inCompare(p.id) ? "✓ In comparison" : "Compare"}</button>
            <button className="btn btn-accent" onClick={askAi}>✨ Ask AI</button>
          </div>

          <div className="notice small">
            {p.is_sample
              ? "ℹ️ This product record, its price, rating and reviews are demo/sample data, not verified market information."
              : `Source: ${p.data_source}`}
            {p.source_url ? (
              <> · <a href={p.source_url} target="_blank" rel="noreferrer noopener">Original product page</a></>
            ) : (
              " · No verified source link is available."
            )}
          </div>
        </div>
      </div>

      <section className="card pad" aria-labelledby="specs-h">
        <h2 id="specs-h" className="h3">Specifications</h2>
        <dl className="specs">
          {Object.entries(p.specs || {}).map(([k, v]) => (
            <div key={k}><dt>{k}</dt><dd>{String(v)}</dd></div>
          ))}
        </dl>
        {p.features?.length ? (
          <div className="chips">{p.features.map((f) => <span key={f} className="chip static">{f}</span>)}</div>
        ) : null}
      </section>

      <section className="card pad" aria-labelledby="price-h">
        <h2 id="price-h" className="h3">Price comparison</h2>
        <p className="muted small">{pc.note}</p>
        {pc.prices.length ? (
          <div className="table-wrap">
            <table className="simple-table">
              <thead>
                <tr><th scope="col">Source</th><th scope="col">Price</th><th scope="col">Status</th><th scope="col">Last updated</th></tr>
              </thead>
              <tbody>
                {pc.prices.map((pr) => (
                  <tr key={pr.id}>
                    <td>{pr.source}</td>
                    <td>{formatPrice(pr.amount, pr.currency)}</td>
                    <td><DataBadge isSample={pr.is_sample} verified={pr.is_verified} label={pr.label} /></td>
                    <td>{formatDate(pr.retrieved_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      <section className="card pad" aria-labelledby="rev-h">
        <div className="section-head">
          <h2 id="rev-h" className="h3">Review summary</h2>
          <button className="btn btn-primary btn-sm" onClick={runAnalysis} disabled={analysisState.loading}>
            {analysisState.loading ? "Analyzing…" : analysis ? "Re-analyze" : `Analyze ${p.review_count} review(s)`}
          </button>
        </div>
        {analysisState.error ? <p className="form-error" role="alert">{analysisState.error}</p> : null}
        {analysis ? <ReviewResult result={analysis} /> : (
          <p className="muted">Summaries are generated only from the reviews stored for this product.</p>
        )}
      </section>
    </div>
  );
}
