import React, { useState, useEffect } from "react";
import axios from "axios";

export default function ProductSearch() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [brand, setBrand] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [sortBy, setSortBy] = useState("name");
  const [results, setResults] = useState([]);

  const API = "http://127.0.0.1:5000";

  const search = async () => {
    try {
      const res = await axios.get(`${API}/search`, {
        params: { q: query, category, brand, min_price: minPrice, max_price: maxPrice, sort_by: sortBy }
      });
      setResults(res.data);
    } catch (err) {
      console.error("Search error:", err);
    }
  };

  // Автокомплит: ищем при изменении query
  useEffect(() => {
    if (query.length >= 2) search();
  }, [query, category, brand, minPrice, maxPrice, sortBy]);

  return (
    <div className="p-3 border mt-4">
      <h3>🔍 Product Search</h3>

      <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search products..." className="border p-1 mb-2" />
      
      <div className="mb-2">
        <input value={category} onChange={e => setCategory(e.target.value)} placeholder="Category" className="border p-1 mr-2"/>
        <input value={brand} onChange={e => setBrand(e.target.value)} placeholder="Brand" className="border p-1"/>
      </div>

      <div className="mb-2">
        <input value={minPrice} onChange={e => setMinPrice(e.target.value)} placeholder="Min price" type="number" className="border p-1 mr-2"/>
        <input value={maxPrice} onChange={e => setMaxPrice(e.target.value)} placeholder="Max price" type="number" className="border p-1"/>
      </div>

      <div className="mb-2">
        <label>Sort by: </label>
        <select value={sortBy} onChange={e => setSortBy(e.target.value)}>
          <option value="name">Name</option>
          <option value="price">Price</option>
          <option value="rating">Rating</option>
        </select>
      </div>

      <ul>
        {results.map((p, i) => (
          <li key={i}>{p.name} — {p.category} — {p.brand} — ${p.price}</li>
        ))}
      </ul>
    </div>
  );
}
