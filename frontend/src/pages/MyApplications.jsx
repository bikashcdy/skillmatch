import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorText } from "../api";
import { Bar, Empty, MatchRing, Skeleton, StatusBadge, timeAgo, useToast, skillLabel } from "../ui.jsx";

export default function MyApplications() {
  const toast = useToast();
  const [apps, setApps] = useState(null);
  useEffect(() => {
    api.get("/my-applications/").then((r) => setApps(r.data.results || r.data))
      .catch((e) => { setApps([]); toast(errorText(e), "err"); });
  }, []);

  return (
    <div className="stack">
      <h1>My applications</h1>
      {apps === null ? <Skeleton /> : apps.length === 0 ? (
        <Empty icon="📝" title="No applications yet">Find a job you like and upload your resume. <Link to="/jobs" style={{ color: "var(--accent)" }}>Browse jobs</Link></Empty>
      ) : apps.map((a) => (
        <div className={`card ${a.status === "selected" ? "success" : ""} ${a.status === "rejected" ? "rejected" : ""}`} key={a.id}>
          <div className="row between" style={{ flexWrap: "nowrap", alignItems: "flex-start" }}>
            <div>
              <h3>{a.job_title} <StatusBadge status={a.status} /></h3>
              <p className="muted">{a.company} · {a.job_location || "—"} · applied {timeAgo(a.created_at)}</p>
            </div>
            <MatchRing value={a.match_percentage} size={72} />
          </div>
          <div className="stack" style={{ marginTop: 14 }}>
            <Bar label="Skills" value={a.skill_score} />
            <Bar label="Experience" value={a.experience_score} />
            <Bar label="Education" value={a.education_score} />
          </div>
          <div style={{ marginTop: 12 }}>
            {a.matched_skills.map((s) => <span className="chip ok" key={s}>✓ {skillLabel(s)}</span>)}
            {a.missing_skills.map((s) => <span className="chip miss" key={s}>✗ {skillLabel(s)}</span>)}
          </div>
          {a.missing_skills.length > 0 && <p className="muted" style={{ marginTop: 8, fontSize: 13 }}>Tip: add the missing skills to your resume if you have them.</p>}
        </div>
      ))}
    </div>
  );
}
