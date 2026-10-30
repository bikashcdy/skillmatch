import { useState } from "react";

// Password input with show/hide button
export function PasswordInput({ value, onChange, placeholder, autoComplete = "new-password", ...rest }) {
  const [show, setShow] = useState(false);
  return (
    <div className="pw">
      <input type={show ? "text" : "password"} value={value} onChange={onChange} placeholder={placeholder}
        autoComplete={autoComplete} {...rest} />
      <button type="button" className="icon-btn" onClick={() => setShow(!show)} aria-label={show ? "Hide password" : "Show password"}>{show ? "🙈" : "👁"}</button>
    </div>
  );
}

// Live checklist: each rule turns green when satisfied
export function Checklist({ rules }) {
  return (
    <ul className="rules">
      {rules.map((r) => <li key={r.label} className={r.ok ? "ok" : ""}><span>{r.ok ? "✓" : "○"}</span>{r.label}</li>)}
    </ul>
  );
}

// Error text under a field
export const FieldError = ({ errors }) => (errors && errors.length ? <p className="field-error">{errors[0]}</p> : null);
