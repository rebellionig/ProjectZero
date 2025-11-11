import React, {useState} from "react";
import { useNavigate } from "react-router-dom";

export default function Login(){
  const [email,setEmail]=useState("");
  const [password,setPassword]=useState("");
  const [twofaToken, setTwofaToken] = useState("");
  const [tmpToken, setTmpToken] = useState(null);
  const nav = useNavigate();

  async function submit(e){
    e.preventDefault();
    const res = await fetch("http://localhost:5000/api/login", {
      method:"POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({email, password})
    });
    const j = await res.json();
    if(res.ok){
      if(j.twofa_required){
        setTmpToken(j.token);
        alert("2FA required. Enter code.");
      } else {
        localStorage.setItem("access_token", j.access_token);
        nav("/profile");
      }
    } else {
      alert(JSON.stringify(j));
    }
  }

  async function verify2fa(e){
    e.preventDefault();
    const res = await fetch("http://localhost:5000/api/verify-2fa", {
      method:"POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({token: tmpToken, code: twofaToken})
    });
    const j = await res.json();
    if(res.ok){
      localStorage.setItem("access_token", j.access_token);
      nav("/profile");
    } else alert(JSON.stringify(j));
  }

  return (
    <div>
      <form onSubmit={submit}>
        <h2>Login</h2>
        <div><input value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email" /></div>
        <div><input value={password} type="password" onChange={e=>setPassword(e.target.value)} placeholder="Password" /></div>
        <button>Login</button>
      </form>

      {tmpToken && (
        <form onSubmit={verify2fa}>
          <h3>Enter 2FA code</h3>
          <input value={twofaToken} onChange={e=>setTwofaToken(e.target.value)} placeholder="123456"/>
          <button>Verify 2FA</button>
        </form>
      )}
    </div>
  )
}
