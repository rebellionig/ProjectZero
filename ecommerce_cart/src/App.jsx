import React, { useState, useEffect } from "react";
import axios from "axios";

const API = "http://127.0.0.1:5000";

export default function App() {
  const [userId] = useState("user123");
  const [productId, setProductId] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [cart, setCart] = useState([]);

  const fetchCart = async () => {
    const res = await axios.get(`${API}/cart/${userId}`);
    setCart(res.data);
  };

  useEffect(() => {
    fetchCart();
  }, []);

  const addToCart = async () => {
    await axios.post(`${API}/cart/add`, { user_id: userId, product_id: productId, quantity });
    fetchCart();
  };

  const removeFromCart = async (id) => {
    await axios.post(`${API}/cart/remove`, { user_id: userId, product_id: id });
    fetchCart();
  };

  const checkout = async () => {
    await axios.post(`${API}/checkout`, { user_id: userId });
    fetchCart();
    alert("Order placed!");
  };

  return (
    <div className="p-6">
      <h1>🛒 Shopping Cart</h1>

      <div className="flex gap-2 mb-4">
        <input
          placeholder="Product ID"
          value={productId}
          onChange={(e) => setProductId(e.target.value)}
        />
        <input
          type="number"
          value={quantity}
          onChange={(e) => setQuantity(parseInt(e.target.value))}
        />
        <button onClick={addToCart}>Add</button>
      </div>

      <h3>Cart:</h3>
      <ul>
        {cart.map((item) => (
          <li key={item.id}>
            {item.name || item.id} x{item.quantity} — ${item.price ?? 0}
            <button onClick={() => removeFromCart(item.id)}>❌</button>
          </li>
        ))}
      </ul>

      <button onClick={checkout}>Checkout</button>
    </div>
  );
}
