import ProductCard from "./ProductCard.jsx";
import { EmptyState, ErrorState, ProductGridSkeleton } from "./StateViews.jsx";

export default function ProductGrid({
  products,
  loading,
  error,
  onRetry,
  emptyTitle = "No products found",
  emptyMessage = "Try changing your search or filters.",
  renderFooter,
}) {
  if (loading) return <ProductGridSkeleton />;
  if (error) return <ErrorState message={error} onRetry={onRetry} />;
  if (!products || products.length === 0)
    return <EmptyState title={emptyTitle} message={emptyMessage} />;
  return (
    <div className="grid">
      {products.map((p) => (
        <ProductCard key={p.id} product={p} footer={renderFooter ? renderFooter(p) : null} />
      ))}
    </div>
  );
}
