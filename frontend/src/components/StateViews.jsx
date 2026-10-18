export function ProductGridSkeleton({ count = 8 }) {
  return (
    <div className="grid" aria-busy="true" aria-label="Loading products">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="card skeleton-card" aria-hidden="true">
          <div className="skeleton img" />
          <div className="skeleton line" />
          <div className="skeleton line short" />
          <div className="skeleton line" />
        </div>
      ))}
    </div>
  );
}

export function Spinner({ label = "Loading…" }) {
  return (
    <div className="spinner-wrap" role="status">
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export function EmptyState({ icon = "🛍️", title, message, action }) {
  return (
    <div className="state empty">
      <div className="state-icon" aria-hidden="true">{icon}</div>
      <h2>{title}</h2>
      {message ? <p className="muted">{message}</p> : null}
      {action}
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="state error" role="alert">
      <div className="state-icon" aria-hidden="true">⚠️</div>
      <h2>We couldn’t load this</h2>
      <p className="muted">{message}</p>
      {onRetry ? (
        <button className="btn btn-primary" onClick={onRetry}>Try again</button>
      ) : null}
    </div>
  );
}
