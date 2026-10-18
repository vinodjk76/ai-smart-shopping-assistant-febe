import { CATEGORY_COLORS, CATEGORY_EMOJI } from "../utils/format";

/** Shows the product image when one exists, otherwise a category-coloured placeholder. */
export default function ProductImage({ product, size = "card" }) {
  const [from, to] = CATEGORY_COLORS[product.category] || ["#64748b", "#334155"];
  if (product.image_url) {
    return (
      <img
        className={`product-img ${size}`}
        src={product.image_url}
        alt={product.name}
        loading="lazy"
      />
    );
  }
  return (
    <div
      className={`product-img placeholder ${size}`}
      style={{ background: `linear-gradient(135deg, ${from}, ${to})` }}
      role="img"
      aria-label={`${product.category} product placeholder`}
    >
      <span aria-hidden="true">{CATEGORY_EMOJI[product.category] || "🛍️"}</span>
    </div>
  );
}
