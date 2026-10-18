import { useState } from "react";
import { NavLink, Link, useNavigate } from "react-router-dom";
import SearchBar from "./SearchBar.jsx";
import { useShop } from "../hooks/useShop.jsx";

const links = [
  { to: "/", label: "Home", end: true },
  { to: "/search", label: "Browse" },
  { to: "/recommendations", label: "AI Picks" },
  { to: "/compare", label: "Compare" },
  { to: "/reviews", label: "Reviews" },
];

export default function Header() {
  const { cart, wishlist, compareIds } = useShop();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const go = (q) => navigate(`/search?q=${encodeURIComponent(q)}`);

  return (
    <header className="header">
      <div className="container header-inner">
        <Link to="/" className="brand" aria-label="AI Smart Shopping Assistant home">
          <span className="brand-mark" aria-hidden="true">🛍️</span>
          <span>SmartCart<b>AI</b></span>
        </Link>

        <div className="header-search">
          <SearchBar onSearch={go} compact />
        </div>

        <div className="header-actions">
          <Link to="/wishlist" className="icon-link" aria-label={`Wishlist, ${wishlist.count} items`}>
            ♡<span className="count">{wishlist.count || 0}</span>
          </Link>
          <Link to="/cart" className="icon-link" aria-label={`Cart, ${cart.item_count} items`}>
            🛒<span className="count">{cart.item_count || 0}</span>
          </Link>
          <button
            className="menu-toggle"
            aria-expanded={open}
            aria-controls="main-nav"
            onClick={() => setOpen((o) => !o)}
          >
            {open ? "✕" : "☰"}<span className="sr-only"> Menu</span>
          </button>
        </div>
      </div>

      <nav id="main-nav" className={`nav ${open ? "open" : ""}`} aria-label="Main">
        <div className="container nav-inner">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              onClick={() => setOpen(false)}
              className={({ isActive }) => (isActive ? "active" : undefined)}
            >
              {l.label}
              {l.to === "/compare" && compareIds.length > 0 ? (
                <span className="pill">{compareIds.length}</span>
              ) : null}
            </NavLink>
          ))}
        </div>
      </nav>
    </header>
  );
}
