import React, { useState, useEffect } from "react";
import axios from "axios";

export default function UserProfile({ userId }) {
  const [user, setUser] = useState({});

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await axios.get(`http://127.0.0.1:5000/users/${userId}`);
        setUser(res.data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchUser();
  }, [userId]);

  return (
    <div className="border p-3 rounded mb-4">
      <h3>👤 User Profile</h3>
      <p>Name: {user.name}</p>
      <p>Email: {user.email}</p>
    </div>
  );
}
