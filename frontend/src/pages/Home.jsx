import React, { useState } from "react";

// User experience
import UserProfile from "../components/UserProfile";
import Wishlist from "../components/Wishlist";
import Cart from "../components/Cart";

// Product
import ProductList from "../pages/product/ProductList";
import ProductForm from "../pages/product/ProductForm";
import Filters from "../pages/product/Filters";

// Recommendation
import ItemRecommendations from "../pages/recommendation/ItemRecommendations";
import SeasonalRecommendations from "../pages/recommendation/SeasonalRecommendations";
import ManualRecommendations from "../pages/recommendation/ManualRecommendations";

// History
import Recommendations from "../pages/history/Recommendations";
import RecommendationsAdvanced from "../pages/history/RecommendationsAdvanced";

// Collaborative filtering
import CFRecommendations from "../pages/collaborative/CFRecommendations";

// Search
import ProductSearch from "../pages/search/ProductSearch";
import SmartSearch from "../pages/search/SmartSearch";

export default function Home() {
  const [userId, setUserId] = useState("user123");
  const [wishlist, setWishlist] = useState([]);
  const [cart, setCart] = useState([]);
  const [filters, setFilters] = useState({ category: "", min_price: "", max_price: "", sort: "name" });

  const addToWishlist = (p) => setWishlist([...wishlist, p]);
  const removeFromWishlist = (p) => setWishlist(wishlist.filter(i => i.id !== p.id));
  const addToCart = (p) => setCart([...cart, p]);
  const removeFromCart = (p) => setCart(cart.filter(i => i.id !== p.id));

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">🛍 E-Commerce Dashboard</h1>

      {/* User profile */}
      <UserProfile userId={userId} />

      {/* Search */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-2">Search Products</h2>
        <ProductSearch />
        <SmartSearch />
      </div>

      {/* Recommendations */}
      <CFRecommendations userId={userId} />
      <Recommendations userId={userId} />
      <RecommendationsAdvanced userId={userId} />
      <ItemRecommendations productId="product123" />
      <SeasonalRecommendations season="winter" />
      <ManualRecommendations />

      {/* Product management */}
      <div className="my-6">
        <Filters filters={filters} setFilters={setFilters} />
        <ProductForm />
        <ProductList filters={filters} />
      </div>

      {/* Wishlist & Cart */}
      <div className="flex gap-6 mt-6">
        <Wishlist items={wishlist} removeFromWishlist={removeFromWishlist} />
        <Cart items={cart} removeFromCart={removeFromCart} />
      </div>
    </div>
  );
}
