import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "../api";

export default function Candidates() {
  const { id } = useParams();
  const [apps, setApps] = useState([]);
  const [msg, setMsg] = useState("");

  const load = () => api.get(`/recruiter/jobs/${id}/candidates/`).then((r) => setApps(r.data));
  useEffect(() => { load(); }, [id]);

  async function selectBest() {
    try {
      const { data } = await api.post(`/recruiter/jobs/${id}/select-best/`);
      setMsg(`Selected ${data.candidate_name} (${data.match_percentage}%)`);
      load();
    } catch {
      setMsg("No applicants to select yet.");
    }
  }

  return (
    <>
      <div className="row between">
        <h1>Ranked candidates</h1>
        <button className="primary" onClick={selectBest}>Select highest match</button>
      </div>
      {msg && <p className="success-text">{msg}</p>}
      {apps.map((a, i) => (
        <div className={`card ${a.status === "selected" ? "success" : ""}`} key={a.id}>
          <div className="row between">
            <h3>#{i + 1} {a.candidate_name} <small>{a.candidate_email}</small></h3>
            <strong className="big">{a.match_percentage}%</strong>
          </div>
          <div className="meter"><div style={{ width: `${a.match_percentage}%` }} /></div>
          <p className="muted">
            Skills {a.skill_score}% · Experience {a.experience_score}% · Education {a.education_score}%
            {a.status === "auto" && " · applied automatically"}
            {a.status === "selected" && " · SELECTED"}
          </p>
          <p>
            {a.matched_skills.map((s) => <span className="chip ok" key={s}>{s}</span>)}
            {a.missing_skills.map((s) => <span className="chip miss" key={s}>missing: {s}</span>)}
          </p>
        </div>
      ))}
    </>
  );
}
