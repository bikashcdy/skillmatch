import { createContext, useCallback, useContext, useEffect, useState } from "react";

/* ---------- toasts ---------- */
const ToastCtx = createContext(() => {});
export const useToast = () => useContext(ToastCtx);

export function ToastProvider({ children }) {
  const [items, setItems] = useState([]);
  const push = useCallback((text, kind = "ok") => {
    const id = Math.random();
    setItems((x) => [...x, { id, text, kind }]);
    setTimeout(() => setItems((x) => x.filter((i) => i.id !== id)), 4200);
  }, []);
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="toasts" aria-live="polite">
        {items.map((t) => <div key={t.id} className={`toast ${t.kind}`}>{t.text}</div>)}
      </div>
    </ToastCtx.Provider>
  );
}

/* ---------- modal ---------- */
export function Modal({ title, onClose, children }) {
  useEffect(() => {
    const k = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [onClose]);
  return (
    <div className="overlay" onMouseDown={onClose}>
      <div className="modal" role="dialog" aria-modal="true" onMouseDown={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h3>{title}</h3>
          <button className="icon-btn" onClick={onClose} aria-label="Close">✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

/* ---------- match ring ---------- */
export function MatchRing({ value, size = 64 }) {
  const r = (size - 8) / 2, c = 2 * Math.PI * r;
  const v = Math.max(0, Math.min(100, value || 0));
  const tone = v >= 75 ? "good" : v >= 50 ? "mid" : "low";
  return (
    <div className={`ring ${tone}`} style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={r} className="ring-bg" />
        <circle cx={size / 2} cy={size / 2} r={r} className="ring-fg"
          strokeDasharray={c} strokeDashoffset={c * (1 - v / 100)}
          transform={`rotate(-90 ${size / 2} ${size / 2})`} />
      </svg>
      <span>{Math.round(v)}%</span>
    </div>
  );
}

export const Bar = ({ label, value }) => (
  <div className="bar">
    <span>{label}</span>
    <div className="meter"><div style={{ width: `${value}%` }} /></div>
    <b>{Math.round(value)}%</b>
  </div>
);

/* ---------- tag input ---------- */
export function TagInput({ value, onChange, placeholder }) {
  const [text, setText] = useState("");
  const add = (raw) => {
    const parts = raw.split(",").map((s) => s.trim()).filter(Boolean);
    if (parts.length) onChange([...new Set([...value, ...parts])]);
    setText("");
  };
  return (
    <div className="taginput">
      {value.map((t) => (
        <span className="chip" key={t}>{t}
          <button type="button" onClick={() => onChange(value.filter((x) => x !== t))} aria-label={`Remove ${t}`}>×</button>
        </span>
      ))}
      <input value={text} placeholder={value.length ? "" : placeholder}
        onChange={(e) => (e.target.value.endsWith(",") ? add(e.target.value) : setText(e.target.value))}
        onKeyDown={(e) => {
          if (e.key === "Enter") { e.preventDefault(); add(text); }
          if (e.key === "Backspace" && !text && value.length) onChange(value.slice(0, -1));
        }}
        onBlur={() => text && add(text)} />
    </div>
  );
}

export const Empty = ({ icon = "📭", title, children }) => (
  <div className="empty"><div className="empty-icon">{icon}</div><h3>{title}</h3><div className="empty-text">{children}</div></div>
);

export const Skeleton = ({ n = 3 }) => (
  <>{Array.from({ length: n }).map((_, i) => <div key={i} className="skeleton" />)}</>
);

export const StatusBadge = ({ status }) => {
  const map = { applied: "Applied", auto: "Auto-applied", selected: "Selected", rejected: "Rejected" };
  return <span className={`badge ${status}`}>{map[status] || status}</span>;
};

export const timeAgo = (iso) => {
  const d = Math.floor((Date.now() - new Date(iso)) / 86400000);
  return d <= 0 ? "today" : d === 1 ? "yesterday" : `${d} days ago`;
};

const SPECIAL = { sql: "SQL", css: "CSS", html: "HTML", aws: "AWS", php: "PHP", "rest api": "REST API",
  "node.js": "Node.js", "c++": "C++", javascript: "JavaScript", typescript: "TypeScript", mongodb: "MongoDB" };
export const skillLabel = (s) => SPECIAL[s] || s.replace(/\b\w/g, (c) => c.toUpperCase());
