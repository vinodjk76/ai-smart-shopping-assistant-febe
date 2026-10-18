import { useState } from "react";
import { Link } from "react-router-dom";
import { api, errorMessage } from "../api/client";
import { useShop } from "../hooks/useShop.jsx";
import { AiBadge } from "../components/DataBadge.jsx";
import ProductCard from "../components/ProductCard.jsx";
import { EmptyState, ErrorState, Spinner } from "../components/StateViews.jsx";
import { NATURAL_EXAMPLES } from "../utils/format";

export default function RecommendationsPage() {
  const { notify } = useShop();
  const [query, setQuery] = useState("");
  const [state, setState] = useState({ loading: false, error: "", data: null });

  const submit = async (text) => {
    const q = (text ?? query).trim();
    if (!q) {
      notify("Please describe what you are looking for", "error");
      return;
    }
    if (q.length > 500) {
      notify("Please keep your request under 500 characters", "error");
      return;
    }
    setQuery(q);
    setState({ loading: true, error: "", data: null });
    try {
      const data = await api.recommend(q, 5);
      setState({ loading: false, error: "", data });
    } catch (err) {
      setState({ loading: false, error: errorMessage(err), data: null });
    }
  };

  const { data } = state;

  return (
    <div className="stack">
      <h1>✨ AI product recommendations</h1>
      <p className="muted">
        Describe your needs, preferences and budget. Products are retrieved from the database and
        ranked; prices, specs and ratings always come from the database, never from the AI.
      </p>

      <form
        className="card pad stack-sm"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <label htmlFor="rec-query">What are you looking for?</label>
        <textarea
          id="rec-query"
          rows={3}
          maxLength={500}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. A laptop for programming under ₹60,000 with a light body"
        />
        <div className="row wrap">
          <button className="btn btn-primary" type="submit" disabled={state.loading}>
            {state.loading ? "Finding…" : "Get recommendations"}
          </button>
          <span className="muted small">{query.length}/500</span>
        </div>
        <div className="chips">
          {NATURAL_EXAMPLES.map((ex) => (
            <button type="button" key={ex} className="chip" onClick={() => submit(ex)}>{ex}</button>
          ))}
        </div>
      </form>

      {state.loading ? <Spinner label="Finding the best matches…" /> : null}
      {state.error ? <ErrorState message={state.error} onRetry={() => submit()} /> : null}

      {data ? (
        <section aria-live="polite" className="stack">
          <div className="section-head">
            <h2>Results</h2>
            <AiBadge aiGenerated={data.ai_generated} source={data.source} />
          </div>
          <p className="notice small">ℹ️ {data.notice}</p>
          {data.parsed?.max_price ? (
            <p className="muted small">Budget detected: up to ₹{Number(data.parsed.max_price).toLocaleString("en-IN")}</p>
          ) : null}

          {data.items.length === 0 ? (
            <EmptyState title="No recommendations" message="Try describing your needs differently."
                        action={<Link to="/search" className="btn btn-primary">Browse products</Link>} />
          ) : (
            <ol className="rec-list">
              {data.items.map((item, i) => (
                <li key={item.product_id} className="rec-item">
                  <div className="rec-rank" aria-label={`Rank ${i + 1}`}>{i + 1}</div>
                  <ProductCard
                    product={item.product}
                    footer={
                      <div className="rec-details">
                        <p><strong>Budget fit:</strong> {item.budget_fit}</p>
                        {item.reasons?.length ? (
                          <>
                            <strong>Why:</strong>
                            <ul>{item.reasons.map((r, j) => <li key={j}>{r}</li>)}</ul>
                          </>
                        ) : null}
                        {item.strengths?.length ? (
                          <>
                            <strong className="pos">Strengths</strong>
                            <ul>{item.strengths.map((r, j) => <li key={j}>{r}</li>)}</ul>
                          </>
                        ) : null}
                        {item.limitations?.length ? (
                          <>
                            <strong className="neg">Limitations</strong>
                            <ul>{item.limitations.map((r, j) => <li key={j}>{r}</li>)}</ul>
                          </>
                        ) : null}
                      </div>
                    }
                  />
                </li>
              ))}
            </ol>
          )}
        </section>
      ) : null}
    </div>
  );
}
