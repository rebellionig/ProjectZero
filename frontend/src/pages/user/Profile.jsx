import React, {useEffect, useState} from "react";
import QRCode from "qrcode.react";

export default function Profile(){
  const [profile,setProfile] = useState(null);
  const [otpUri, setOtpUri] = useState(null);
  const token = localStorage.getItem("access_token");

  useEffect(()=>{
    if(!token) return;
    fetch("http://localhost:5000/api/profile", {headers: {"Authorization": "Bearer "+token}})
      .then(r=>r.json()).then(j=> setProfile(j));
  },[]);

  async function setup2fa(){
    const res = await fetch("http://localhost:5000/api/setup-2fa", {method:"POST", headers: {"Authorization":"Bearer "+token}});
    const j = await res.json();
    if(res.ok){
      setOtpUri(j.otp_uri);
    } else alert(JSON.stringify(j));
  }

  if(!token) return <div>Please login</div>;
  if(!profile) return <div>Loading...</div>;
  return (
    <div>
      <h2>Profile</h2>
      <div>Name: {profile.full_name}</div>
      <div>Email: {profile.email} (verified: {String(profile.is_verified)})</div>
      <div>Phone: {profile.phone}</div>
      <div>Privacy: {profile.privacy}</div>

      <button onClick={setup2fa}>Enable 2FA</button>
      {otpUri && (
        <div>
          <p>Scan this QR with Google Authenticator / Authy:</p>
          <QRCode value={otpUri} />
        </div>
      )}
    </div>
  )
}
