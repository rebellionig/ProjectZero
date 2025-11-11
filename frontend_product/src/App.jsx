import React from "react";
import ProductList from "./components/ProductList";
import ProductForm from "./components/ProductForm";

export default function App() {
  return (
    <div className="p-4">
      <h1>🛒 Product Catalog</h1>
      <ProductForm />
      <hr />
      <ProductList />
    </div>
  );
}
