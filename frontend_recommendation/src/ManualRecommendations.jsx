import React, { useEffect, useState } from "react";
import axios from "axios";

export default function ManualRecommendations() {
  const [recs, setRecs] = useState([]);
  const API = "http://127.0.0.1:5000";

  useEffect(() => {
    const fetchRecs = async () => {
      const res = await axios.get(`${API}/recommend/manual`);
      setRecs(res.data);
    };
    fetchRecs();
  }, []);

  return (
    <div>
      <h3>⚡ Admin Boosted Products</h3>
      <ul>
        {recs.map((p, i) => (
          <li key={i}>{p.name} — {p.category} — ${p.price} (weight: {p.weight})</li>
        ))}
      </ul>
    </div>
  );
}
