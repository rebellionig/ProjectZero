import React, { useState, useEffect } from "react";
import axios from "axios";

export default function ReviewSection({ sku }) {
  const [reviews, setReviews] = useState([]);
  const [rating, setRating] = useState("");
  const [comment, setComment] = useState("");
  const [average, setAverage] = useState(0);

  const fetchReviews = async () => {
    const res = await axios.get(`http://127.0.0.1:5000/products/${sku}/reviews`);
    setReviews(res.data.reviews);
    setAverage(res.data.average_rating);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!rating) return alert("Please enter a rating!");
    await axios.post(`http://127.0.0.1:5000/products/${sku}/reviews`, {
      rating,
      comment,
    });
    setRating("");
    setComment("");
    fetchReviews();
  };

  useEffect(() => {
    fetchReviews();
  }, [sku]);

  return (
    <div className="border-t mt-2 pt-2">
      <h4 className="font-semibold">
        Reviews (Average rating: {average || "No reviews"})
      </h4>
      <ul>
        {reviews.map((r, idx) => (
          <li key={idx} className="text-sm border-b py-1">
            ⭐ {r.rating} — {r.comment}
          </li>
        ))}
      </ul>

      <form onSubmit={handleSubmit} className="mt-2 flex flex-col gap-1">
        <input
          type="number"
          min="1"
          max="5"
          value={rating}
          onChange={(e) => setRating(e.target.value)}
          placeholder="Rating (1–5)"
          className="border p-1 rounded"
        />
        <input
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Comment"
          className="border p-1 rounded"
        />
        <button
          type="submit"
          className="bg-green-500 text-white rounded px-2 py-1 mt-1"
        >
          Add Review
        </button>
      </form>
    </div>
  );
}
