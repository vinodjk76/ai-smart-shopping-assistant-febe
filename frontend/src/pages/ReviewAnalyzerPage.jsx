import { useState } from "react";
import { api, errorMessage } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { AiBadge } from "../components/DataBadge.jsx";
import { Spinner } from "../components/StateViews.jsx";

function List({ title, items, tone }) {
  if (!items?.length) return null;
  return (
    <div>
      <h3 className={`h4 ${tone || ""}`}>{title}</h3>
      <ul>{items.map((t, i) => <li key={i}>{t}</li>)}</ul>
    </div>
  );
}

/** Shared by the Review Analyzer page and the Product Details page. */
export function ReviewResult({ result }) {
  return (
    <div className="stack-sm" aria-live="polite">
      <div className="row wrap">
        <strong>{result.reviews_analyzed} review(s) analyzed</strong>
        <AiBadge aiGenerated={result.ai_generated} source={result.source} />
        {result.is_sample_data ? <span className="badge badge-sample">Sample reviews</span> : null}
      </div>
      <p className={result.reliable ? "notice small" : "warn small"} role={result.reliable ? undefined : "note"}>
        {result.reliable ? "ℹ️" : "⚠️"} {result.reliability_note}
      </p>
      <p>{result.summary}</p>
      <div className="three-col">
        <List title="Positive points" items={result.positives} tone="pos" />
        <List title="Negative points" items={result.negatives} tone="neg" />
        <List title="Common complaints" items={result.common_complaints} />
      </div>
      {result.source === "rules" ? (
        <p className="muted small">
          AI is unavailable, so this summary was produced by a keyword-based analysis of the supplied reviews, not by Gemini.
        </p>
      ) : null}
    </div>
  );
}

export default function ReviewAnalyzerPage() {
  const catalogue = useAsync(() => api.products({ per_page: 50, sort: "name" }), []);
  const [mode, setMode] = useState("product");
  const [productId, setProductId] = useState("");
  const [text, setText] = useState("");
  const [state, setState] = useState({ loading: false, error: "", result: null });

  const run = async (e) => {
    e.preventDefault();
    let payload;
    if (mode === "product") {
      if (!productId) return setState({ loading: false, error: "Please choose a product.", result: null });
      payload = { product_id: Number(productId) };
    } else {
      if (!text.trim()) return setState({ loading: false, error: "Please paste at least one review.", result: null });
      if (text.length > 8000) return setState({ loading: false, error: "Text is too long (max 8000 characters).", result: null });
      payload = { text };
    }
    setState({ loading: true, error: "", result: null });
    try {
      setState({ loading: false, error: "", result: await api.analyzeReviews(payload) });
    } catch (err) {
      setState({ loading: false, error: errorMessage(err), result: null });
    }
  };

  return (
    <div className="stack">
      <h1>AI review analyzer</h1>
      <p className="muted">
        Conclusions are based only on the reviews supplied. Separate pasted reviews with a blank line
        (or one per line).
      </p>

      <form className="card pad stack-sm" onSubmit={run}>
        <div className="tabs" role="tablist" aria-label="Review source">
          <button type="button" role="tab" aria-selected={mode === "product"}
                  className={mode === "product" ? "tab active" : "tab"} onClick={() => setMode("product")}>
            Product reviews
          </button>
          <button type="button" role="tab" aria-selected={mode === "text"}
                  className={mode === "text" ? "tab active" : "tab"} onClick={() => setMode("text")}>
            Paste my own
          </button>
        </div>

        {mode === "product" ? (
          <label>
            Product
            <select value={productId} onChange={(e) => setProductId(e.target.value)} disabled={catalogue.loading}>
              <option value="">Choose a product…</option>
              {(catalogue.data?.items || []).map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </label>
        ) : (
          <label>
            Reviews
            <textarea rows={8} maxLength={8000} value={text} onChange={(e) => setText(e.target.value)}
                      placeholder={"Battery lasts two days, love it.\n\nCamera is average in low light."} />
          </label>
        )}

        <div>
          <button className="btn btn-primary" type="submit" disabled={state.loading}>
            {state.loading ? "Analyzing…" : "Analyze reviews"}
          </button>
        </div>
      </form>

      {state.loading ? <Spinner label="Analyzing reviews…" /> : null}
      {state.error ? <p className="form-error" role="alert">{state.error}</p> : null}
      {state.result ? (
        <section className="card pad">
          <h2 className="h3">Analysis{state.result.product_name ? `: ${state.result.product_name}` : ""}</h2>
          <ReviewResult result={state.result} />
        </section>
      ) : null}
    </div>
  );
}
