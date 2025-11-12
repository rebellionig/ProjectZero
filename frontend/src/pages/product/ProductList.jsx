import React, { useEffect, useState } from "react";
import axios from "axios";
import ReviewSection from "./ReviewSection";

export default function ProductList({ filters }) {
  const [products, setProducts] = useState([]);
  const [openSku, setOpenSku] = useState(null);

  const fetchProducts = async () => {
    const params = new URLSearchParams(filters);
    const res = await axios.get(`http://127.0.0.1:5000/products?${params}`);
    setProducts(res.data);
  };

  useEffect(() => {
    fetchProducts();
  }, [filters]);

  return (
    <div>
      <h2 className="text-xl font-semibold mb-2">Available Products</h2>
      {products.length === 0 ? (
        <p>No products found.</p>
      ) : (
        <ul className="space-y-2">
          {products.map((p, idx) => (
            <li
              key={idx}
              className="border rounded p-3 bg-gray-50"
            >
              <div className="flex justify-between">
                <div>
                  <strong>{p.name}</strong> — {p.category}<br />
                  ${p.price} — {p.description}
                </div>
                <button
                  className="text-blue-500 underline"
                  onClick={() => setOpenSku(openSku === p.sku ? null : p.sku)}
                >
                  {openSku === p.sku ? "Hide Reviews" : "Show Reviews"}
                </button>
              </div>
              {openSku === p.sku && <ReviewSection sku={p.sku} />}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
