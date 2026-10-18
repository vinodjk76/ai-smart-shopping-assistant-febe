import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import SearchBar from "../components/SearchBar.jsx";
import FilterSidebar, { EMPTY_FILTERS } from "../components/FilterSidebar.jsx";
import ProductGrid from "../components/ProductGrid.jsx";
import { NATURAL_EXAMPLES, formatPrice } from "../utils/format";

const PER_PAGE = 12;

export default function SearchPage() {
  const [params, setParams] = useSearchParams();

  const q = params.get("q") || "";
  const page = Math.max(1, parseInt(params.get("page") || "1", 10) || 1);
  const filters = useMemo(
    () => ({
      category: params.get("category") || "",
      brand: params.get("brand") || "",
      min_price: params.get("min_price") || "",
      max_price: params.get("max_price") || "",
      min_rating: params.get("min_rating") || "",
      sort: params.get("sort") || "",
      in_stock: params.get("in_stock") === "true",
    }),
    [params]
  );

  const meta = useAsync(() => api.categories(), []);

  const key = params.toString();
  const { data, loading, error, reload } = useAsync(() => {
    const query = { page, per_page: PER_PAGE };
    if (q) query.q = q;
    Object.entries(filters).forEach(([k, v]) => {
      if (v !== "" && v !== false) query[k] = v === true ? "true" : v;
    });
    return api.products(query);
  }, [key]);

  const update = (next) => {
    const p = new URLSearchParams();
    if (next.q) p.set("q", next.q);
    Object.entries(next.filters).forEach(([k, v]) => {
      if (v !== "" && v !== false) p.set(k, v === true ? "true" : v);
    });
    setParams(p);
  };

  const interp = data?.interpreted_query || {};
  const interpretedBits = [];
  if (interp.categories?.length) interpretedBits.push(`category: ${interp.categories.join(", ")}`);
  if (interp.max_price) interpretedBits.push(`max price: ${formatPrice(interp.max_price)}`);
  if (interp.min_price) interpretedBits.push(`min price: ${formatPrice(interp.min_price)}`);
  if (interp.keywords?.length) interpretedBits.push(`keywords: ${interp.keywords.join(", ")}`);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PER_PAGE)) : 1;
  const goPage = (n) => {
    const p = new URLSearchParams(params);
    p.set("page", String(n));
    setParams(p);
    window.scrollTo?.({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="stack">
      <h1>Browse products</h1>
      <SearchBar initial={q} onSearch={(text) => update({ q: text, filters })} />
      <div className="chips">
        {NATURAL_EXAMPLES.map((ex) => (
          <button key={ex} className="chip" onClick={() => update({ q: ex, filters: EMPTY_FILTERS })}>{ex}</button>
        ))}
      </div>

      <div className="layout-sidebar">
        <FilterSidebar
          filters={filters}
          categories={meta.data?.categories}
          brands={meta.data?.brands}
          onChange={(f) => update({ q, filters: f })}
        />

        <section aria-live="polite">
          {data ? (
            <div className="results-meta">
              <strong>{data.total}</strong> product{data.total === 1 ? "" : "s"} found
              {interpretedBits.length ? (
                <span className="muted"> · understood “{q}” as {interpretedBits.join(" · ")}</span>
              ) : null}
              <div className="notice small">ℹ️ {data.data_notice}</div>
            </div>
          ) : null}

          <ProductGrid
            products={data?.items}
            loading={loading}
            error={error}
            onRetry={reload}
            emptyMessage="No products matched. Try different words, or clear some filters."
          />

          {data && totalPages > 1 ? (
            <nav className="pagination" aria-label="Pagination">
              <button className="btn btn-ghost" disabled={page <= 1} onClick={() => goPage(page - 1)}>← Previous</button>
              <span>Page {page} of {totalPages}</span>
              <button className="btn btn-ghost" disabled={page >= totalPages} onClick={() => goPage(page + 1)}>Next →</button>
            </nav>
          ) : null}
        </section>
      </div>
    </div>
  );
}
