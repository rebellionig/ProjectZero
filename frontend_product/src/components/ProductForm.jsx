import React, { useState } from "react";
import axios from "axios";

export default function ProductForm() {
  const [form, setForm] = useState({
    name: "",
    description: "",
    category: "",
    price: "",
    sku: "",
  });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await axios.post("http://127.0.0.1:5000/products", form);
    alert("Product created!");
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="name" placeholder="Name" onChange={handleChange} />
      <input name="description" placeholder="Description" onChange={handleChange} />
      <input name="category" placeholder="Category" onChange={handleChange} />
      <input name="price" type="number" placeholder="Price" onChange={handleChange} />
      <input name="sku" placeholder="SKU" onChange={handleChange} />
      <button type="submit">Add Product</button>
    </form>
  );
}
