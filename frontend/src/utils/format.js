export function formatPrice(amount, currency = "INR") {
  if (amount === null || amount === undefined) return "Price unavailable";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: currency || "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatDate(iso) {
  if (!iso) return "unknown";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "unknown" : d.toLocaleString();
}

export const CATEGORY_EMOJI = {
  Smartphones: "📱",
  Laptops: "💻",
  Headphones: "🎧",
  "Home Appliances": "🏠",
  Accessories: "🔌",
};

export const CATEGORY_COLORS = {
  Smartphones: ["#6366f1", "#8b5cf6"],
  Laptops: ["#0ea5e9", "#2563eb"],
  Headphones: ["#ec4899", "#f43f5e"],
  "Home Appliances": ["#10b981", "#0d9488"],
  Accessories: ["#f59e0b", "#f97316"],
};

/** Validate quantity input on the client (the server validates again). */
export function validQuantity(value, max = 10) {
  const n = Number(value);
  return Number.isInteger(n) && n >= 1 && n <= max;
}

export const NATURAL_EXAMPLES = [
  "Find the best headphones under ₹3,000",
  "Recommend a laptop for programming under ₹60,000",
  "Compare smartphones with good battery life",
];
