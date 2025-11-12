import React, { useState, useEffect } from "react";
import axios from "axios";

export default function SmartSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [sortBy, setSortBy] = useState("score");

  const API = "http://127.0.0.1:5000";

  const search = async () => {
    if (!query) return;
    try {
      const res = await axios.get(`${API}/search/fulltext`, {
        params: { q: query, min_price: minPrice, max_price: maxPrice, sort_by: sortBy }
      });
      setResults(res.data);
    } catch (err) {
      console.error("Fulltext search error:", err);
    }
  };

  // Автокомплит и поиск при вводе >2 символов
  useEffect(() => {
    if (query.length >= 2) search();
  }, [query, minPrice, maxPrice, sortBy]);

  return (
    <div className="p-3 border mt-4">
      <h3>🔎 Smart Search (Full-text + Fuzzy)</h3>
      <input
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder="Search products..."
        className="border p-1 mb-2"
      />
      <div className="mb-2">
        <input value={minPrice} onChange={e => setMinPrice(e.target.value)} placeholder="Min price" type="number" className="border p-1 mr-2"/>
        <input value={maxPrice} onChange={e => setMaxPrice(e.target.value)} placeholder="Max price" type="number" className="border p-1"/>
      </div>
      <ul>
        {results.map((p, i) => (
          <li key={i}>
            {p.name} — {p.category} — {p.brand} — ${p.price} (score: {p.score.toFixed(2)})
          </li>
        ))}
      </ul>
    </div>
  );
}
