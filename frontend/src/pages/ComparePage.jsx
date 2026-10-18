import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useShop } from "../hooks/useShop.jsx";
import ComparisonTable from "../components/ComparisonTable.jsx";
import { AiBadge } from "../components/DataBadge.jsx";
import { EmptyState, ErrorState, Spinner } from "../components/StateViews.jsx";
import { formatDate, formatPrice } from "../utils/format";

export default function ComparePage() {
  const { compareIds, toggleCompare, clearCompare, maxCompare } = useShop();
  const catalogue = useAsync(() => api.products({ per_page: 50, sort: "name" }), []);
  const key = compareIds.join(",");
  const { data, loading, error, reload } = useAsync(
    () => (compareIds.length >= 2 ? api.compare(compareIds) : Promise.resolve(null)),
    [key]
  );

  const options = (catalogue.data?.items || []).filter((p) => !compareIds.includes(p.id));

  return (
    <div className="stack">
      <h1>Compare products</h1>

      <div className="card pad row wrap">
        <label className="grow">
          Add a product ({compareIds.length}/{maxCompare} selected)
          <select
            value=""
            disabled={compareIds.length >= maxCompare || catalogue.loading}
            onChange={(e) => e.target.value && toggleCompare(Number(e.target.value))}
          >
            <option value="">Choose a product…</option>
            {options.map((p) => (
              <option key={p.id} value={p.id}>{p.name} — {formatPrice(p.price)}</option>
            ))}
          </select>
        </label>
        {compareIds.length ? (
          <button className="btn btn-ghost" onClick={clearCompare}>Clear all</button>
        ) : null}
      </div>

      {compareIds.length < 2 ? (
        <EmptyState
          icon="⚖️"
          title="Select at least two products"
          message="Use the dropdown above, or press “Compare” on any product card."
          action={<Link to="/search" className="btn btn-primary">Browse products</Link>}
        />
      ) : loading ? (
        <Spinner label="Comparing products…" />
      ) : error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : data ? (
        <>
          <section className="card pad" aria-labelledby="sum-h">
            <div className="section-head">
              <h2 id="sum-h" className="h3">Summary</h2>
              <AiBadge aiGenerated={data.ai_generated} source={data.source} />
            </div>
            <p>{data.summary.text}</p>
            {data.summary.key_differences?.length ? (
              <>
                <h3 className="h4">Key differences</h3>
                <ul>{data.summary.key_differences.map((d, i) => <li key={i}>{d}</li>)}</ul>
              </>
            ) : null}
            {data.summary.value_for_money?.length ? (
              <>
                <h3 className="h4">Value for money</h3>
                <ul>{data.summary.value_for_money.map((d, i) => <li key={i}>{d}</li>)}</ul>
              </>
            ) : null}
            {data.summary.best_value ? (
              <p>
                <strong>Best value according to Gemini: </strong>
                {data.products.find((p) => p.id === data.summary.best_value.product_id)?.name}
                {data.summary.best_value.why ? ` — ${data.summary.best_value.why}` : ""}
              </p>
            ) : null}
            <p className="muted small">{data.notice}</p>
          </section>

          <ComparisonTable products={data.products} rows={data.rows} highlights={data.highlights} />

          <section className="card pad" aria-labelledby="pc-h">
            <h2 id="pc-h" className="h3">Price sources</h2>
            <p className="muted small">
              {Object.values(data.price_comparisons).some((c) => c.has_verified_prices)
                ? "Verified prices show their source and retrieval time."
                : "No live retailer API is configured: only sample (demo) prices are available."}
            </p>
            <div className="table-wrap">
              <table className="simple-table">
                <thead>
                  <tr><th scope="col">Product</th><th scope="col">Source</th><th scope="col">Price</th><th scope="col">Status</th><th scope="col">Updated</th></tr>
                </thead>
                <tbody>
                  {data.products.flatMap((p) =>
                    data.price_comparisons[String(p.id)].prices.map((pr) => (
                      <tr key={`${p.id}-${pr.id}`}>
                        <td>{p.name}</td>
                        <td>{pr.source}</td>
                        <td>{formatPrice(pr.amount, pr.currency)}</td>
                        <td>{pr.label}</td>
                        <td>{formatDate(pr.retrieved_at)}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}
