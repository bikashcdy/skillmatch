import { useState } from "react";
import { Link } from "react-router-dom";
import api, { errorText } from "../api";
import { FieldError } from "../ui_extra.jsx";
import { emailErrors } from "../validate.js";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [err, setErr] = useState([]);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    const errors = emailErrors(email);
    setErr(errors);
    if (errors.length) return;
    setBusy(true);
    try { await api.post("/auth/forgot-password/", { email: email.trim() }); setDone(true); }
    catch (ex) { setErr([errorText(ex)]); }
    setBusy(false);
  }

  return (
    <form className="card narrow stack" onSubmit={submit} noValidate>
      <h2>Forgot your password?</h2>
      {done ? (
        <>
          <p className="success-text">Check your email.</p>
          <p className="muted">If <b>{email}</b> has an account, we sent a link to choose a new password. It works for 3 days. Also look in your Spam folder.</p>
          <Link className="btn" to="/login">Back to log in</Link>
        </>
      ) : (
        <>
          <p className="muted">Enter the email you registered with and we will send you a reset link.</p>
          <div><input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className={err.length ? "bad" : ""} autoFocus />
            <FieldError errors={err} /></div>
          <button className="primary" disabled={busy}>{busy ? "Sending…" : "Send reset link"}</button>
          <Link to="/login" className="muted" style={{ textAlign: "center" }}>Back to log in</Link>
        </>
      )}
    </form>
  );
}
