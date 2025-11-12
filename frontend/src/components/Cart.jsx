import React from "react";
import ProductCard from "./ProductCard";

export default function Cart({ items, removeFromCart }) {
  return (
    <div>
      <h3>🛒 Cart</h3>
      {items.length === 0 ? <p>Cart is empty.</p> :
        items.map(p => <ProductCard key={p.id} product={p} onAddToCart={() => {}} onAddToWishlist={() => removeFromCart(p)} />)
      }
    </div>
  );
}
