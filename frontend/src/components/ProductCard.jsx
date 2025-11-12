import React from "react";

export default function ProductCard({ product, onAddToCart, onAddToWishlist }) {
  return (
    <div className="border p-3 rounded shadow hover:shadow-lg transition-all mb-4">
      <h4 className="font-bold">{product.name}</h4>
      <p>{product.category} — {product.brand}</p>
      <p>${product.price}</p>
      <div className="mt-2 flex gap-2">
        <button className="px-2 py-1 bg-blue-500 text-white rounded" onClick={() => onAddToCart(product)}>Add to Cart</button>
        <button className="px-2 py-1 bg-yellow-500 text-white rounded" onClick={() => onAddToWishlist(product)}>Wishlist</button>
      </div>
    </div>
  );
}
