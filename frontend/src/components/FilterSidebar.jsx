import { useEffect, useState } from "react";

export const EMPTY_FILTERS = {
  category: "",
  brand: "",
  min_price: "",
  max_price: "",
  min_rating: "",
  sort: "",
  in_stock: false,
};

export default function FilterSidebar({ filters, onChange, categories = [], brands = [] }) {
  const [draft, setDraft] = useState(filters);
  const [error, setError] = useState("");

  useEffect(() => setDraft(filters), [filters]);

  const set = (key, value) => setDraft((d) => ({ ...d, [key]: value }));

  const apply = (e) => {
    e.preventDefault();
    const min = draft.min_price === "" ? null : Number(draft.min_price);
    const max = draft.max_price === "" ? null : Number(draft.max_price);
    if ((min !== null && (Number.isNaN(min) || min < 0)) || (max !== null && (Number.isNaN(max) || max < 0))) {
      setError("Prices must be positive numbers.");
      return;
    }
    if (min !== null && max !== null && min > max) {
      setError("Minimum price cannot be greater than maximum price.");
      return;
    }
    setError("");
    onChange(draft);
  };

  const reset = () => {
    setError("");
    onChange(EMPTY_FILTERS);
  };

  return (
    <form className="card filters" onSubmit={apply} aria-label="Product filters">
      <h2 className="h3">Filters</h2>

      <label>
        Sort by
        <select value={draft.sort} onChange={(e) => set("sort", e.target.value)}>
          <option value="">Best match</option>
          <option value="price_asc">Price: low to high</option>
          <option value="price_desc">Price: high to low</option>
          <option value="rating">Rating</option>
          <option value="name">Name (A–Z)</option>
        </select>
      </label>

      <label>
        Category
        <select value={draft.category} onChange={(e) => set("category", e.target.value)}>
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c.name} value={c.name}>{c.name} ({c.count})</option>
          ))}
        </select>
      </label>

      <label>
        Brand
        <select value={draft.brand} onChange={(e) => set("brand", e.target.value)}>
          <option value="">All brands</option>
          {brands.map((b) => (
            <option key={b} value={b}>{b}</option>
          ))}
        </select>
      </label>

      <fieldset>
        <legend>Price (₹)</legend>
        <div className="row">
          <input type="number" min="0" inputMode="numeric" placeholder="Min" aria-label="Minimum price"
                 value={draft.min_price} onChange={(e) => set("min_price", e.target.value)} />
          <input type="number" min="0" inputMode="numeric" placeholder="Max" aria-label="Maximum price"
                 value={draft.max_price} onChange={(e) => set("max_price", e.target.value)} />
        </div>
      </fieldset>

      <label>
        Minimum rating
        <select value={draft.min_rating} onChange={(e) => set("min_rating", e.target.value)}>
          <option value="">Any</option>
          <option value="3">3★ &amp; up</option>
          <option value="4">4★ &amp; up</option>
          <option value="4.5">4.5★ &amp; up</option>
        </select>
      </label>

      <label className="check">
        <input type="checkbox" checked={draft.in_stock} onChange={(e) => set("in_stock", e.target.checked)} />
        In stock only
      </label>

      {error ? <p className="form-error" role="alert">{error}</p> : null}

      <div className="row">
        <button type="submit" className="btn btn-primary">Apply</button>
        <button type="button" className="btn btn-ghost" onClick={reset}>Reset</button>
      </div>
    </form>
  );
}
