import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { errorText, login } from "../api";
import { useT } from "../i18n.jsx";

export default function Register() {
  const { t } = useT();
  const [form, setForm] = useState({ username: "", email: "", password: "", role: "candidate", company_name: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/auth/register/", form);
      await login(form.username, form.password);
      navigate("/");
      window.location.reload();
    } catch (err) {
      setError(errorText(err, "Registration failed."));
      setBusy(false);
    }
  }

  return (
    <div className="auth">
      <div className="auth-side">
        <h1>{t("joinTitle")}</h1>
        <ul>
          <li><b>Candidates</b> — find jobs by skill and location</li>
          <li><b>Recruiters</b> — post jobs, rank applicants automatically</li>
        </ul>
      </div>
      <form className="auth-form" onSubmit={submit}>
        <h2>{t("createAccount")}</h2>
        {error && <p className="error">{error}</p>}
        <div className="seg">
          {["candidate", "recruiter"].map((r) => (
            <button type="button" key={r} className={form.role === r ? "on" : ""} onClick={() => setForm({ ...form, role: r })}>
              {r === "candidate" ? t("lookingJob") : t("hiring")}
            </button>
          ))}
        </div>
        <input placeholder={t("username")} value={form.username} onChange={set("username")} required />
        <input type="email" placeholder={t("email")} value={form.email} onChange={set("email")} required />
        <input type="password" placeholder={t("passwordMin")} minLength={8} value={form.password} onChange={set("password")} required />
        {form.role === "recruiter" && <input placeholder={t("company")} value={form.company_name} onChange={set("company_name")} required />}
        <button className="primary" disabled={busy}>{busy ? t("creating") : t("createAccount")}</button>
        <p className="muted">{t("haveAccount")} <Link to="/login" style={{ color: "var(--accent)", fontWeight: 600 }}>{t("login")}</Link></p>
      </form>
    </div>
  );
}
