import { useShop } from "../hooks/useShop.jsx";

export default function Toasts() {
  const { toasts, dismissToast } = useShop();
  return (
    <div className="toasts" role="status" aria-live="polite">
      {toasts.map((t) => (
        <div key={t.id} className={`toast ${t.type}`}>
          <span>{t.message}</span>
          <button onClick={() => dismissToast(t.id)} aria-label="Dismiss notification">✕</button>
        </div>
      ))}
    </div>
  );
}
