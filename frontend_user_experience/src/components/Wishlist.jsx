import React from "react";
import ProductCard from "./ProductCard";

export default function Wishlist({ items, removeFromWishlist }) {
  return (
    <div>
      <h3>💖 Wishlist</h3>
      {items.length === 0 ? <p>No items in wishlist.</p> :
        items.map(p => <ProductCard key={p.id} product={p} onAddToCart={() => {}} onAddToWishlist={() => removeFromWishlist(p)} />)
      }
    </div>
  );
}
