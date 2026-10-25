import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login } from "../api";

export default function Login() {
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function submit(e) {
    e.preventDefault();
    try {
      await login(form.username, form.password);
      navigate("/");
      window.location.reload();
    } catch {
      setError("Invalid username or password.");
    }
  }

  return (
    <form className="card narrow" onSubmit={submit}>
      <h2>Log in</h2>
      {error && <p className="error">{error}</p>}
      <input placeholder="Username" value={form.username}
             onChange={(e) => setForm({ ...form, username: e.target.value })} required />
      <input type="password" placeholder="Password" value={form.password}
             onChange={(e) => setForm({ ...form, password: e.target.value })} required />
      <button className="primary">Log in</button>
      <p>No account? <Link to="/register">Register</Link></p>
    </form>
  );
}
