import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, errorMessage } from "../api/client";

const ShopContext = createContext(null);
const MAX_COMPARE = 4;

export function ShopProvider({ children }) {
  const [cart, setCart] = useState({ items: [], total: 0, item_count: 0, currency: "INR" });
  const [wishlist, setWishlist] = useState({ items: [], count: 0 });
  const [toasts, setToasts] = useState([]);
  const [compareIds, setCompareIds] = useState(() => {
    try {
      const saved = JSON.parse(sessionStorage.getItem("compareIds") || "[]");
      return Array.isArray(saved) ? saved.slice(0, MAX_COMPARE) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try {
      sessionStorage.setItem("compareIds", JSON.stringify(compareIds));
    } catch {
      /* storage unavailable: ignore */
    }
  }, [compareIds]);

  const notify = useCallback((message, type = "success") => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, message, type }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000);
  }, []);

  const dismissToast = useCallback((id) => setToasts((t) => t.filter((x) => x.id !== id)), []);

  const refresh = useCallback(async () => {
    try {
      const [c, w] = await Promise.all([api.cart(), api.wishlist()]);
      setCart(c);
      setWishlist(w);
    } catch (err) {
      notify(errorMessage(err), "error");
    }
  }, [notify]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const guard = useCallback(
    async (fn, okMessage) => {
      try {
        const result = await fn();
        if (okMessage) notify(okMessage);
        return result;
      } catch (err) {
        notify(errorMessage(err), "error");
        return null;
      }
    },
    [notify]
  );

  const value = useMemo(
    () => ({
      cart,
      wishlist,
      toasts,
      notify,
      dismissToast,
      compareIds,
      maxCompare: MAX_COMPARE,
      isWishlisted: (productId) => wishlist.items.some((i) => i.product_id === productId),
      inCompare: (productId) => compareIds.includes(productId),
      toggleCompare: (productId) => {
        setCompareIds((ids) => {
          if (ids.includes(productId)) return ids.filter((i) => i !== productId);
          if (ids.length >= MAX_COMPARE) {
            notify(`You can compare up to ${MAX_COMPARE} products`, "error");
            return ids;
          }
          return [...ids, productId];
        });
      },
      clearCompare: () => setCompareIds([]),
      addToCart: async (productId, quantity = 1) => {
        const data = await guard(() => api.addToCart(productId, quantity), "Added to cart");
        if (data) setCart(data);
      },
      updateQuantity: async (itemId, quantity) => {
        const data = await guard(() => api.updateCartItem(itemId, quantity));
        if (data) setCart(data);
      },
      removeFromCart: async (itemId) => {
        const data = await guard(() => api.removeCartItem(itemId), "Removed from cart");
        if (data) setCart(data);
      },
      toggleWishlist: async (productId) => {
        const existing = wishlist.items.find((i) => i.product_id === productId);
        const data = existing
          ? await guard(() => api.removeWishlistItem(existing.id), "Removed from wishlist")
          : await guard(() => api.addToWishlist(productId), "Saved to wishlist");
        if (data) setWishlist(data);
      },
      removeFromWishlist: async (itemId) => {
        const data = await guard(() => api.removeWishlistItem(itemId), "Removed from wishlist");
        if (data) setWishlist(data);
      },
    }),
    [cart, wishlist, toasts, compareIds, notify, dismissToast, guard]
  );

  return <ShopContext.Provider value={value}>{children}</ShopContext.Provider>;
}

export function useShop() {
  const ctx = useContext(ShopContext);
  if (!ctx) throw new Error("useShop must be used inside <ShopProvider>");
  return ctx;
}
