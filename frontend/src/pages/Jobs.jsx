import { useEffect, useState } from "react";
import api from "../api";

export default function Jobs() {
  const [jobs, setJobs] = useState([]);
  const [q, setQ] = useState("");
  const [applying, setApplying] = useState(null);
  const [file, setFile] = useState(null);
  const [auto, setAuto] = useState(true);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const load = () => api.get("/jobs/", { params: { q } }).then((r) => setJobs(r.data.results || r.data));
  useEffect(() => { load(); }, []);

  async function apply(job) {
    setError("");
    const body = new FormData();
    if (file) body.append("resume", file);
    body.append("auto_apply_related", auto);
    try {
      const { data } = await api.post(`/jobs/${job.id}/apply/`, body);
      setResult(data);
      setApplying(null);
      setFile(null);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not apply.");
    }
  }

  return (
    <>
      <h1>Open jobs</h1>
      <div className="row">
        <input placeholder="Search by title" value={q} onChange={(e) => setQ(e.target.value)} />
        <button onClick={load}>Search</button>
      </div>

      {result && (
        <div className="card success">
          <h3>Applied. Your match results:</h3>
          {result.map((a) => (
            <p key={a.id}>
              <strong>{a.job_title}</strong> at {a.company}: <strong>{a.match_percentage}%</strong>
              {a.status === "auto" && <span className="badge">auto-applied</span>}
            </p>
          ))}
        </div>
      )}

      {jobs.map((job) => (
        <div className="card" key={job.id}>
          <h3>{job.title} <small>at {job.company}</small></h3>
          <p>{job.description}</p>
          <p>
            {job.required_skills.map((s) => <span className="chip" key={s}>{s}</span>)}
          </p>
          <p className="muted">
            {job.location} · {job.min_experience_years}+ yrs · {job.required_education || "any education"}
          </p>
          {applying === job.id ? (
            <div className="apply-box">
              <input type="file" accept=".pdf,.docx,.txt,.png,.jpg,.jpeg" onChange={(e) => setFile(e.target.files[0])} />
              <label>
                <input type="checkbox" checked={auto} onChange={(e) => setAuto(e.target.checked)} />
                Also apply to other related jobs that match my resume
              </label>
              {error && <p className="error">{error}</p>}
              <button className="primary" onClick={() => apply(job)}>Submit application</button>
              <button onClick={() => setApplying(null)}>Cancel</button>
            </div>
          ) : (
            <button className="primary" onClick={() => setApplying(job.id)}>Apply</button>
          )}
        </div>
      ))}
    </>
  );
}
