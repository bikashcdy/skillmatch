import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { errorText, login } from "../api";
import { useT } from "../i18n.jsx";

export default function Login() {
  const { t } = useT();
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
        <h1>{t("heroTitle")}</h1>
        <ul>
          <li>Upload a resume, see your match % instantly</li>
          <li>Auto-apply to related jobs</li>
          <li>Recruiters get candidates ranked by fit</li>
        </ul>
      </div>
      <form className="auth-form" onSubmit={submit}>
        <h2>{t("welcomeBack")}</h2>
        {error && <p className="error">{error}</p>}
        <div><label className="f">{t("username")}</label>
          <input value={form.username} autoFocus onChange={(e) => setForm({ ...form, username: e.target.value })} required /></div>
        <div><label className="f">{t("password")}</label>
          <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required /></div>
        <button className="primary" disabled={busy}>{busy ? t("signingIn") : t("login")}</button>
        <p className="muted">{t("noAccount")} <Link to="/register" style={{ color: "var(--accent)", fontWeight: 600 }}>{t("createOne")}</Link></p>
      </form>
    </div>
  );
}
