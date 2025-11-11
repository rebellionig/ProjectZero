import React, { useState } from "react";
import UserProfile from "./components/UserProfile";
import ProductSearch from "./components/ProductSearch";
import SmartSearch from "./components/SmartSearch";
import CFRecommendations from "./components/CFRecommendations";
import Wishlist from "./components/Wishlist";
import Cart from "./components/Cart";

export default function App() {
  const [userId, setUserId] = useState("user123");
  const [wishlist, setWishlist] = useState([]);
  const [cart, setCart] = useState([]);

  const addToWishlist = (product) => setWishlist([...wishlist, product]);
  const removeFromWishlist = (product) => setWishlist(wishlist.filter(p => p.id !== product.id));
  const addToCart = (product) => setCart([...cart, product]);
  const removeFromCart = (product) => setCart(cart.filter(p => p.id !== product.id));

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">🛍 E-Commerce SPA</h1>

      <UserProfile userId={userId} />

      <div className="mb-4">
        <h2 className="text-xl font-semibold mb-2">Search Products</h2>
        <ProductSearch />
        <SmartSearch />
      </div>

      <CFRecommendations userId={userId} />

      <div className="mt-6 flex gap-6">
        <Wishlist items={wishlist} removeFromWishlist={removeFromWishlist} />
        <Cart items={cart} removeFromCart={removeFromCart} />
      </div>
    </div>
  );
}
