import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import api, { errorText } from "../api";
import { Checklist, FieldError, PasswordInput } from "../ui_extra.jsx";
import { passwordOk, passwordRules } from "../validate.js";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const uid = params.get("uid"), token = params.get("token");
  const [pw, setPw] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);
  const valid = passwordOk(pw, "", "") && pw === confirm;

  async function submit(e) {
    e.preventDefault();
    if (!valid) return;
    setBusy(true);
    try { await api.post("/auth/reset-password/", { uid, token, password: pw }); setDone(true); }
    catch (ex) { setError(errorText(ex)); }
    setBusy(false);
  }

  if (!uid || !token) {
    return <div className="card narrow stack"><h2>Link problem</h2><p className="error">This reset link is incomplete. Open the link from your email again, or ask for a new one.</p>
      <Link className="btn" to="/forgot-password">Request a new link</Link></div>;
  }
  return (
    <form className="card narrow stack" onSubmit={submit}>
      <h2>Choose a new password</h2>
      {done ? (
        <><p className="success-text">Your password was changed.</p><Link className="btn primary" to="/login">Log in</Link></>
      ) : (
        <>
          {error && <p className="error">{error} <Link to="/forgot-password" style={{ textDecoration: "underline" }}>Request a new link</Link></p>}
          <div><PasswordInput placeholder="New password" value={pw} onChange={(e) => setPw(e.target.value)} />
            <Checklist rules={passwordRules(pw)} /></div>
          <div><PasswordInput placeholder="Confirm new password" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
            <FieldError errors={confirm && confirm !== pw ? ["Passwords do not match."] : []} /></div>
          <button className="primary" disabled={busy || !valid}>{busy ? "Saving…" : "Change password"}</button>
        </>
      )}
    </form>
  );
}
