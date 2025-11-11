import React from "react";

export default function Filters({ filters, setFilters }) {
  const handleChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      <input
        name="category"
        placeholder="Category"
        value={filters.category}
        onChange={handleChange}
        className="border rounded p-1"
      />
      <input
        name="min_price"
        type="number"
        placeholder="Min price"
        value={filters.min_price}
        onChange={handleChange}
        className="border rounded p-1"
      />
      <input
        name="max_price"
        type="number"
        placeholder="Max price"
        value={filters.max_price}
        onChange={handleChange}
        className="border rounded p-1"
      />
      <select
        name="sort"
        value={filters.sort}
        onChange={handleChange}
        className="border rounded p-1"
      >
        <option value="name">Sort by name</option>
        <option value="price">Sort by price</option>
      </select>
    </div>
  );
}
