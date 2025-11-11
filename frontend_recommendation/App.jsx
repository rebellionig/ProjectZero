import React, { useState } from "react";
import ItemRecommendations from "./ItemRecommendations";
import SeasonalRecommendations from "./SeasonalRecommendations";
import ManualRecommendations from "./ManualRecommendations";

export default function App() {
  const [productId, setProductId] = useState("product123");
  const [season, setSeason] = useState("winter");

  return (
    <div className="p-6">
      <h1>🤖 Recommendation Engine</h1>
      
      <div className="mb-4">
        <input value={productId} onChange={e => setProductId(e.target.value)} placeholder="Product ID" />
      </div>

      <ItemRecommendations productId={productId} />
      <SeasonalRecommendations season={season} />
      <ManualRecommendations />
    </div>
  );
}
