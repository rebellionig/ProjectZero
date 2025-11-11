import React, { useState, useEffect } from "react";
import axios from "axios";
import Recommendations from "./Recommendations";
import RecommendationsAdvanced from "./RecommendationsAdvanced";

const API = "http://127.0.0.1:5000";

export default function App() {
  const [userId] = useState("user123");
  const [productId, setProductId] = useState("");
  const [history, setHistory] = useState([]);

  const fetchHistory = async () => {
    const res = await axios.get(`${API}/history/${userId}`);
    setHistory(res.data);
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const act = async (endpoint) => {
    await axios.post(`${API}/${endpoint}`, { user_id: userId, product_id: productId });
    fetchHistory();
  };

  return (
    <div className="p-6">
      <h1>🧾 User History & Wishlist</h1>
      {/* Actions & History */}
      <Recommendations userId={userId} />
      <RecommendationsAdvanced userId={userId} />
      <div>
        <input
          placeholder="Product ID"
          value={productId}
          onChange={(e) => setProductId(e.target.value)}
        />
        <button onClick={() => act("view")}>👀 View</button>
        <button onClick={() => act("like")}>❤️ Like</button>
        <button onClick={() => act("wishlist/add")}>⭐ Add to Wishlist</button>
        <button onClick={() => act("wishlist/remove")}>❌ Remove</button>
        <button onClick={() => act("purchase")}>🛒 Purchase</button>
        <button onClick={() => act("return")}>↩️ Return</button>
      </div>

      <h3>История действий:</h3>
      <ul>
        {history.map((h, i) => (
          <li key={i}>
            [{h.action}] product: {h.product_id} at {h.time || "—"}
          </li>
        ))}
      </ul>
    </div>
  );
}
