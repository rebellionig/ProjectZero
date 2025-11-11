import React, { useState, useEffect } from "react";
import axios from "axios";

export default function CFRecommendations({ userId }) {
  const [algo, setAlgo] = useState("user_based");
  const [recs, setRecs] = useState([]);
  const [limit, setLimit] = useState(10);

  const API = "http://127.0.0.1:5000";

  const fetchRecommendations = async () => {
    try {
      const res = await axios.get(`${API}/cf/recommend/${userId}`, {
        params: { algo, limit }
      });
      setRecs(res.data);
    } catch (err) {
      console.error("Error fetching CF recommendations:", err);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [algo, limit]);

  return (
    <div className="p-3 border mt-4">
      <h3>📊 Collaborative Filtering Recommendations</h3>

      <div className="mb-3">
        <label>Algorithm: </label>
        <select value={algo} onChange={e => setAlgo(e.target.value)}>
          <option value="user_based">User-based CF</option>
          <option value="item_based">Item-based CF</option>
        </select>
      </div>

      <div className="mb-3">
        <label>Limit: </label>
        <input type="number" value={limit} min={1} max={50} onChange={e => setLimit(e.target.value)} />
      </div>

      <button onClick={fetchRecommendations} className="mb-3 px-3 py-1 bg-blue-500 text-white rounded">
        Refresh Recommendations
      </button>

      <ul>
        {recs.map((p, i) => (
          <li key={i}>
            {p.name} — {p.category} — ${p.price} (score: {p.score || 0})
          </li>
        ))}
      </ul>
    </div>
  );
}
