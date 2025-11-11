import React, { useEffect, useState } from "react";
import axios from "axios";

export default function SeasonalRecommendations({ season }) {
  const [recs, setRecs] = useState([]);
  const API = "http://127.0.0.1:5000";

  useEffect(() => {
    const fetchRecs = async () => {
      const res = await axios.get(`${API}/recommend/seasonal`, { params: { season } });
      setRecs(res.data);
    };
    fetchRecs();
  }, [season]);

  return (
    <div>
      <h3>🌟 Seasonal / Promo</h3>
      <ul>
        {recs.map((p, i) => (
          <li key={i}>{p.name} — {p.category} — ${p.price}</li>
        ))}
      </ul>
    </div>
  );
}
