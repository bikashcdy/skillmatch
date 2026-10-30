import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { errorText, login } from "../api";
import { useT } from "../i18n.jsx";
import { Checklist, FieldError, PasswordInput } from "../ui_extra.jsx";
import { companyErrors, emailErrors, passwordOk, passwordRules, usernameErrors } from "../validate.js";

export default function Register() {
  const { t } = useT();
  const [form, setForm] = useState({ username: "", email: "", password: "", confirm: "", role: "candidate", company_name: "" });
  const [touched, setTouched] = useState({});
  const [taken, setTaken] = useState({ username: [], email: [] });   // answers from the server (already used?)
  const [serverErrors, setServerErrors] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const set = (k) => (e) => { setForm({ ...form, [k]: e.target.value }); setServerErrors({ ...serverErrors, [k]: null }); };
  const blur = (k) => () => setTouched({ ...touched, [k]: true });

  // Ask the server if the username / email is free, half a second after the user stops typing.
  useEffect(() => {
    const u = form.username.trim(), e = form.email.trim();
    const body = {};
    if (!usernameErrors(u).length) body.username = u;
    if (!emailErrors(e).length) body.email = e;
    if (!Object.keys(body).length) { setTaken({ username: [], email: [] }); return; }
    const id = setTimeout(() => {
      api.post("/auth/check/", body).then((r) => setTaken((p) => ({ username: body.username ? r.data.username || [] : [], email: body.email ? r.data.email || [] : [] }))).catch(() => {});
    }, 500);
    return () => clearTimeout(id);
  }, [form.username, form.email]);

  const errs = {
    username: serverErrors.username || [...usernameErrors(form.username), ...(usernameErrors(form.username).length ? [] : taken.username)],
    email: serverErrors.email || [...emailErrors(form.email), ...(emailErrors(form.email).length ? [] : taken.email)],
    company_name: serverErrors.company_name || (form.role === "recruiter" ? companyErrors(form.company_name) : []),
    confirm: form.confirm && form.confirm !== form.password ? ["Passwords do not match."] : [],
  };
  const rules = passwordRules(form.password, form.username.trim(), form.email.trim());
  const valid = !errs.username.length && !errs.email.length && !errs.company_name.length &&
    passwordOk(form.password, form.username.trim(), form.email.trim()) && form.password === form.confirm && form.confirm !== "";
  const show = (k) => (touched[k] || serverErrors[k] ? errs[k] : []);

  async function submit(e) {
    e.preventDefault();
    setTouched({ username: true, email: true, company_name: true, confirm: true, password: true });
    if (!valid) return;
    setBusy(true);
    setError("");
    try {
      const { confirm, ...body } = form;
      await api.post("/auth/register/", { ...body, username: body.username.trim(), email: body.email.trim() });
      await login(form.username.trim(), form.password);
      navigate("/");
      window.location.reload();
    } catch (err) {
      const d = err.response?.data;
      if (d && typeof d === "object" && !d.detail) {
        const se = {};
        Object.entries(d).forEach(([k, v]) => { se[k] = [].concat(v); });
        setServerErrors(se);
        if (se.non_field_errors) setError(se.non_field_errors.join(" "));
      } else setError(errorText(err, "Registration failed."));
      setBusy(false);
    }
  }

  return (
    <div className="auth">
      <div className="auth-side">
        <h1>{t("joinTitle")}</h1>
        <ul>
          <li><b>Candidates</b> — find jobs by skill and location</li>
          <li><b>Recruiters</b> — post jobs, rank applicants automatically (an admin approves new recruiters)</li>
        </ul>
      </div>
      <form className="auth-form" onSubmit={submit} noValidate>
        <h2>{t("createAccount")}</h2>
        {error && <p className="error">{error}</p>}
        <div className="seg">
          {["candidate", "recruiter"].map((r) => (
            <button type="button" key={r} className={form.role === r ? "on" : ""} onClick={() => setForm({ ...form, role: r })}>
              {r === "candidate" ? t("lookingJob") : t("hiring")}
            </button>
          ))}
        </div>
        <div>
          <input placeholder={`${t("username")} (4-20 letters, numbers, _)`} value={form.username} onChange={set("username")} onBlur={blur("username")}
            className={show("username").length ? "bad" : ""} autoComplete="username" maxLength={30} />
          <FieldError errors={show("username")} />
        </div>
        <div>
          <input type="email" placeholder={t("email")} value={form.email} onChange={set("email")} onBlur={blur("email")}
            className={show("email").length ? "bad" : ""} autoComplete="email" />
          <FieldError errors={show("email")} />
        </div>
        {form.role === "recruiter" && (
          <div>
            <input placeholder={t("company")} value={form.company_name} onChange={set("company_name")} onBlur={blur("company_name")}
              className={show("company_name").length ? "bad" : ""} maxLength={100} />
            <FieldError errors={show("company_name")} />
          </div>
        )}
        <div>
          <PasswordInput placeholder={t("password")} value={form.password} onChange={set("password")} onBlur={blur("password")} />
          {(touched.password || form.password) && <Checklist rules={rules} />}
          <FieldError errors={serverErrors.password} />
        </div>
        <div>
          <PasswordInput placeholder="Confirm password" value={form.confirm} onChange={set("confirm")} onBlur={blur("confirm")} />
          <FieldError errors={show("confirm")} />
        </div>
        <button className="primary" disabled={busy}>{busy ? t("creating") : t("createAccount")}</button>
        <p className="muted">{t("haveAccount")} <Link to="/login" style={{ color: "var(--accent)", fontWeight: 600 }}>{t("login")}</Link></p>
      </form>
    </div>
  );
}
