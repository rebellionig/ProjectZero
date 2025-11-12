import React, { useEffect, useState } from "react";
import axios from "axios";

export default function Recommendations({ userId }) {
  const [recs, setRecs] = useState([]);
  const API = "http://127.0.0.1:5000";

  const fetchRecs = async () => {
    const res = await axios.get(`${API}/recommend/${userId}`);
    setRecs(res.data);
  };

  useEffect(() => {
    fetchRecs();
  }, [userId]);

  if (recs.length === 0) return <p>No recommendations yet.</p>;

  return (
    <div className="mt-4 border p-3">
      <h3 className="font-semibold">🎯 Recommended for you:</h3>
      <ul>
        {recs.map((p, i) => (
          <li key={i}>
            {p.name} — {p.category} — ${p.price}
          </li>
        ))}
      </ul>
    </div>
  );
}
