import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000/api";

const http = axios.create({ baseURL, timeout: 30000 });

/** Turn any axios failure into a friendly Error with a readable message. */
export function errorMessage(err) {
  if (err?.response?.data?.error?.message) return err.response.data.error.message;
  if (err?.code === "ECONNABORTED") return "The request timed out. Please try again.";
  if (err?.message === "Network Error")
    return "Cannot reach the server. Make sure the Flask backend is running.";
  return err?.message || "Something went wrong.";
}

const get = (url, params) => http.get(url, { params }).then((r) => r.data);
const post = (url, body) => http.post(url, body).then((r) => r.data);
const patch = (url, body) => http.patch(url, body).then((r) => r.data);
const del = (url) => http.delete(url).then((r) => r.data);

export const api = {
  health: () => get("/health"),
  products: (params) => get("/products", params),
  product: (id) => get(`/products/${id}`),
  categories: () => get("/categories"),
  recommend: (query, limit = 5) => post("/recommendations", { query, limit }),
  compare: (productIds) => post("/compare", { product_ids: productIds }),
  analyzeReviews: (payload) => post("/reviews/analyze", payload),
  cart: () => get("/cart"),
  addToCart: (productId, quantity = 1) =>
    post("/cart/items", { product_id: productId, quantity }),
  updateCartItem: (itemId, quantity) => patch(`/cart/items/${itemId}`, { quantity }),
  removeCartItem: (itemId) => del(`/cart/items/${itemId}`),
  wishlist: () => get("/wishlist"),
  addToWishlist: (productId) => post("/wishlist/items", { product_id: productId }),
  removeWishlistItem: (itemId) => del(`/wishlist/items/${itemId}`),
  chat: (message, history) => post("/chat", { message, history }),
};
