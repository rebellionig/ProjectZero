import React from "react";
import { useLocation, useNavigate } from "react-router-dom";

export default function VerifyEmail(){
  const loc = useLocation();
  const params = new URLSearchParams(loc.search);
  const token = params.get("token");
  const nav = useNavigate();

  async function go(){
    const res = await fetch("http://localhost:5000/api/verify-email", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({token})});
    const j = await res.json();
    if(res.ok){
      alert("Verified!");
      nav("/");
    } else alert(JSON.stringify(j));
  }

  return (
    <div>
      <h2>Verify Email</h2>
      <button onClick={go}>Verify</button>
    </div>
  )
}
