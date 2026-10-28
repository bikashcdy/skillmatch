import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api, { errorText } from "../api";
import { Bar, Empty, MatchRing, Skeleton, StatusBadge, useToast, skillLabel } from "../ui.jsx";

export default function Candidates() {
  const { id } = useParams();
  const toast = useToast();
  const [apps, setApps] = useState(null);
  const [open, setOpen] = useState(null);

  const load = () => api.get(`/recruiter/jobs/${id}/candidates/`).then((r) => setApps(r.data))
    .catch((e) => { setApps([]); toast(errorText(e, "Could not load candidates."), "err"); });
  useEffect(() => { load(); }, [id]);

  async function selectBest() {
    try {
      const { data } = await api.post(`/recruiter/jobs/${id}/select-best/`);
      toast(`Selected ${data.candidate_name} (${data.match_percentage}%)`); load();
    } catch (e) { toast(errorText(e), "err"); }
  }
  async function setStatus(a, status) {
    try { await api.post(`/recruiter/applications/${a.id}/status/`, { status }); load(); }
    catch (e) { toast(errorText(e), "err"); }
  }

  return (
    <div className="stack">
      <Link to="/recruiter" className="muted">← Back to my jobs</Link>
      <div className="row between">
        <div><h1>Ranked candidates</h1><p className="muted">Highest match first</p></div>
        <button className="primary" onClick={selectBest} disabled={!apps?.length}>★ Select highest match</button>
      </div>
      {apps === null ? <Skeleton /> : apps.length === 0 ? (
        <Empty icon="📭" title="No applicants yet">Candidates who apply (or are auto-matched) will appear here, ranked.</Empty>
      ) : apps.map((a, i) => (
        <div className={`card ${a.status === "selected" ? "success" : ""} ${a.status === "rejected" ? "rejected" : ""}`} key={a.id}>
          <div className="row between" style={{ flexWrap: "nowrap" }}>
            <div className="row" style={{ flexWrap: "nowrap" }}>
              <div className="logo">#{i + 1}</div>
              <div><h3>{a.candidate_name} <StatusBadge status={a.status} /></h3>
                <p className="muted">{a.candidate_email} · {a.candidate_experience} yrs · {a.candidate_education}</p></div>
            </div>
            <MatchRing value={a.match_percentage} size={72} />
          </div>
          <div style={{ marginTop: 10 }}>
            {a.matched_skills.map((s) => <span className="chip ok" key={s}>✓ {skillLabel(s)}</span>)}
            {a.missing_skills.map((s) => <span className="chip miss" key={s}>missing: {skillLabel(s)}</span>)}
          </div>
          {open === a.id && (
            <div className="stack" style={{ marginTop: 12 }}>
              <Bar label="Skills" value={a.skill_score} /><Bar label="Experience" value={a.experience_score} /><Bar label="Education" value={a.education_score} />
              <div><small>Skills found in resume:</small><br />{a.candidate_skills.map((s) => <span className="chip" key={s}>{skillLabel(s)}</span>)}</div>
            </div>
          )}
          <div className="row" style={{ marginTop: 14 }}>
            <button onClick={() => setOpen(open === a.id ? null : a.id)}>{open === a.id ? "Hide details" : "Details"}</button>
            {a.resume_url && <a className="btn" href={a.resume_url} target="_blank" rel="noreferrer">📄 Resume</a>}
            {a.status !== "selected" && <button className="primary" onClick={() => setStatus(a, "selected")}>Select</button>}
            {a.status !== "rejected" ? <button className="danger" onClick={() => setStatus(a, "rejected")}>Reject</button>
              : <button onClick={() => setStatus(a, "applied")}>Restore</button>}
          </div>
        </div>
      ))}
    </div>
  );
}
