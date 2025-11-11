import React, {useState} from "react";
import { useNavigate } from "react-router-dom";

export default function Register(){
  const [email,setEmail]=useState("");
  const [password,setPassword]=useState("");
  const [name,setName]=useState("");
  const [phone,setPhone]=useState("");
  const nav = useNavigate();

  async function submit(e){
    e.preventDefault();
    const res = await fetch("http://localhost:5000/api/register", {
      method:"POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({email, password, full_name: name, phone})
    });
    const j = await res.json();
    if(res.ok){
      alert("Registered! Check email for verification (or look at backend logs).");
      nav("/");
    } else {
      alert(JSON.stringify(j));
    }
  }

  return (
    <form onSubmit={submit}>
      <h2>Register</h2>
      <div><input required placeholder="Full name" value={name} onChange={e=>setName(e.target.value)} /></div>
      <div><input required placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} /></div>
      <div><input required type="password" placeholder="Password" value={password} onChange={e=>setPassword(e.target.value)} /></div>
      <div><input placeholder="Phone" value={phone} onChange={e=>setPhone(e.target.value)} /></div>
      <button type="submit">Register</button>
    </form>
  )
}
