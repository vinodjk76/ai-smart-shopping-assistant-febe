import { Route, Routes } from "react-router-dom";
import Header from "./components/Header.jsx";
import ChatWidget from "./components/ChatWidget.jsx";
import Toasts from "./components/Toasts.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import SearchPage from "./pages/SearchPage.jsx";
import ProductDetails from "./pages/ProductDetails.jsx";
import ComparePage from "./pages/ComparePage.jsx";
import RecommendationsPage from "./pages/RecommendationsPage.jsx";
import ReviewAnalyzerPage from "./pages/ReviewAnalyzerPage.jsx";
import CartPage from "./pages/CartPage.jsx";
import WishlistPage from "./pages/WishlistPage.jsx";
import NotFound from "./pages/NotFound.jsx";

export default function App() {
  return (
    <>
      <a className="skip-link" href="#main">Skip to content</a>
      <Header />
      <main id="main" className="container" tabIndex={-1}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/products/:id" element={<ProductDetails />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
          <Route path="/reviews" element={<ReviewAnalyzerPage />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/wishlist" element={<WishlistPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <footer className="footer">
        Demo app · Product data, prices, ratings and reviews are sample data, not verified
        market information · No real payments are processed.
      </footer>
      <ChatWidget />
      <Toasts />
    </>
  );
}
