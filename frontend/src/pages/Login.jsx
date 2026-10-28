import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { errorText, login } from "../api";

export default function Login() {
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await login(form.username.trim(), form.password);
      navigate("/");
      window.location.reload();
    } catch (err) {
      setError(err.response?.status === 401 ? "Invalid username or password." : errorText(err));
      setBusy(false);
    }
  }

  return (
    <div className="auth">
      <div className="auth-side">
        <h1>Hire smarter.<br />Get matched faster.</h1>
        <ul>
          <li>Upload a resume, see your match % instantly</li>
          <li>Auto-apply to related jobs</li>
          <li>Recruiters get candidates ranked by fit</li>
        </ul>
      </div>
      <form className="auth-form" onSubmit={submit}>
        <h2>Welcome back</h2>
        {error && <p className="error">{error}</p>}
        <div><label className="f">Username</label>
          <input value={form.username} autoFocus onChange={(e) => setForm({ ...form, username: e.target.value })} required /></div>
        <div><label className="f">Password</label>
          <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required /></div>
        <button className="primary" disabled={busy}>{busy ? "Signing in…" : "Log in"}</button>
        <p className="muted">No account? <Link to="/register" style={{ color: "var(--accent)", fontWeight: 600 }}>Create one</Link></p>
      </form>
    </div>
  );
}
