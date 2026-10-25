import { useEffect, useState } from "react";
import api from "../api";

export default function MyApplications() {
  const [apps, setApps] = useState([]);
  useEffect(() => {
    api.get("/my-applications/").then((r) => setApps(r.data.results || r.data));
  }, []);

  return (
    <>
      <h1>My applications</h1>
      {apps.length === 0 && <p className="muted">No applications yet.</p>}
      {apps.map((a) => (
        <div className="card" key={a.id}>
          <h3>{a.job_title} <small>at {a.company}</small></h3>
          <div className="meter"><div style={{ width: `${a.match_percentage}%` }} /></div>
          <p><strong>{a.match_percentage}% match</strong> · status: {a.status}</p>
          <p>
            {a.matched_skills.map((s) => <span className="chip ok" key={s}>{s}</span>)}
            {a.missing_skills.map((s) => <span className="chip miss" key={s}>missing: {s}</span>)}
          </p>
        </div>
      ))}
    </>
  );
}
