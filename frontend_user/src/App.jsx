import React from "react";
import { Outlet, Link } from "react-router-dom";

export default function App(){
  return (
    <div style={{padding:20}}>
      <nav>
        <Link to="/">Login</Link> | <Link to="/register">Register</Link> | <Link to="/profile">Profile</Link>
      </nav>
      <hr/>
      <Outlet/>
    </div>
  )
}
