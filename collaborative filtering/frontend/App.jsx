import React, { useState } from "react";
import CFRecommendations from "./CFRecommendations";

export default function App() {
  const [userId, setUserId] = useState("user123");

  return (
    <div className="p-6">
      <h1>🤖 CF Engine Demo</h1>

      <div className="mb-4">
        <input
          value={userId}
          onChange={e => setUserId(e.target.value)}
          placeholder="User ID"
          className="border p-1"
        />
      </div>

      <CFRecommendations userId={userId} />
    </div>
  );
}
