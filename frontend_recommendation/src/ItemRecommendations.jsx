import React, { useEffect, useState } from "react";
import axios from "axios";

export default function ItemRecommendations({ productId }) {
  const [recs, setRecs] = useState([]);
  const API = "http://127.0.0.1:5000";

  useEffect(() => {
    const fetchRecs = async () => {
      const res = await axios.get(`${API}/recommend/item/${productId}`);
      setRecs(res.data);
    };
    fetchRecs();
  }, [productId]);

  return (
    <div>
      <h3>🔗 Similar Products</h3>
      <ul>
        {recs.map((p, i) => (
          <li key={i}>{p.name} — {p.category} — ${p.price}</li>
        ))}
      </ul>
    </div>
  );
}
