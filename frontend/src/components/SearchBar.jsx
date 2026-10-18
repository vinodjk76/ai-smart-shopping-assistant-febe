import { useEffect, useState } from "react";

export default function SearchBar({ onSearch, initial = "", compact = false, placeholder }) {
  const [value, setValue] = useState(initial);

  useEffect(() => setValue(initial), [initial]);

  const submit = (e) => {
    e.preventDefault();
    const q = value.trim();
    if (q.length > 200) return;
    onSearch(q);
  };

  return (
    <form className={`searchbar ${compact ? "compact" : ""}`} onSubmit={submit} role="search">
      <label htmlFor={compact ? "search-compact" : "search-main"} className="sr-only">
        Search products
      </label>
      <input
        id={compact ? "search-compact" : "search-main"}
        type="search"
        value={value}
        maxLength={200}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder || "Search products, brands or ask e.g. “headphones under ₹3,000”"}
      />
      <button type="submit" className="btn btn-primary">Search</button>
    </form>
  );
}
