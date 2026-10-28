import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorText } from "../api";
import { Empty, Modal, Skeleton, TagInput, timeAgo, useToast, skillLabel } from "../ui.jsx";

const empty = { title: "", description: "", location: "", skills: [], min_experience_years: 0, required_education: "" };

export default function RecruiterDashboard() {
  const toast = useToast();
  const [jobs, setJobs] = useState(null);
  const [form, setForm] = useState(null);
  const [busy, setBusy] = useState(false);
  const [cities, setCities] = useState([]);
  useEffect(() => { api.get("/jobs/meta/").then((x) => setCities(x.data.cities.map((c) => c.name))); }, []);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const load = () => api.get("/recruiter/jobs/").then((r) => setJobs(r.data.results || r.data))
    .catch((e) => { setJobs([]); toast(errorText(e), "err"); });
  useEffect(() => { load(); }, []);

  async function save(e) {
    e.preventDefault();
    if (!form.skills.length) return toast("Add at least one required skill.", "err");
    setBusy(true);
    const body = { ...form, location: (form.location || "").trim(), required_skills: form.skills, min_experience_years: Number(form.min_experience_years) || 0 };
    try {
      if (form.id) await api.put(`/recruiter/jobs/${form.id}/`, body);
      else await api.post("/recruiter/jobs/", body);
      toast(form.id ? "Job updated" : "Job published");
      setForm(null); load();
    } catch (err) { toast(errorText(err, "Failed to save job."), "err"); }
    setBusy(false);
  }
  const toggle = async (j) => { await api.patch(`/recruiter/jobs/${j.id}/`, { is_open: !j.is_open }); load(); };
  const remove = async (j) => {
    if (!window.confirm(`Delete "${j.title}" and all its applications?`)) return;
    await api.delete(`/recruiter/jobs/${j.id}/`); toast("Job deleted"); load();
  };

  const total = (jobs || []).reduce((n, j) => n + j.applicants, 0);
  return (
    <div className="stack">
      <div className="row between">
        <div><h1>My jobs</h1><p className="muted">{jobs ? `${jobs.length} posted · ${total} applicants` : ""}</p></div>
        <button className="primary" onClick={() => setForm(empty)}>＋ Post a job</button>
      </div>
      {jobs === null ? <Skeleton /> : jobs.length === 0 ? (
        <Empty icon="🧑‍💼" title="You haven't posted a job yet">Post a job with its required skills and JobMitra will rank every applicant for you.</Empty>
      ) : jobs.map((j) => (
        <div className="card" key={j.id} style={{ opacity: j.is_open ? 1 : .65 }}>
          <div className="row between">
            <div>
              <h3>{j.title} {!j.is_open && <span className="badge">Closed</span>}</h3>
              <p className="muted">📍 {j.location || "—"} · {j.min_experience_years}+ yrs · posted {timeAgo(j.created_at)} · <b>{j.applicants}</b> applicant(s)</p>
              <div style={{ marginTop: 8 }}>{j.required_skills.map((s) => <span className="chip" key={s}>{skillLabel(s)}</span>)}</div>
            </div>
            <div className="row">
              <Link className="btn primary" to={`/recruiter/jobs/${j.id}`}>Ranked candidates</Link>
              <button onClick={() => setForm({ ...j, skills: j.required_skills })}>Edit</button>
              <button onClick={() => toggle(j)}>{j.is_open ? "Close" : "Reopen"}</button>
              <button className="danger" onClick={() => remove(j)}>Delete</button>
            </div>
          </div>
        </div>
      ))}
      {form && (
        <Modal title={form.id ? "Edit job" : "Post a job"} onClose={() => setForm(null)}>
          <form className="stack" onSubmit={save}>
            <div><label className="f">Job title</label><input value={form.title} onChange={set("title")} required /></div>
            <div><label className="f">Description</label><textarea value={form.description} onChange={set("description")} required /></div>
            <div><label className="f">Location</label>
              <select value={cities.includes(form.location) ? form.location : form.location ? "__other" : ""}
                onChange={(e) => setForm({ ...form, location: e.target.value === "__other" ? " " : e.target.value })}>
                <option value="">Select a city</option>
                {cities.map((c) => <option key={c} value={c}>{c}</option>)}
                <option value="__other">Other city…</option>
              </select>
              {!cities.includes(form.location) && form.location !== "" && (
                <input style={{ marginTop: 8 }} placeholder="Type the city or town" value={form.location.trim() === "" ? "" : form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value || " " })} />
              )}</div>
            <div><label className="f">Required skills (press Enter after each)</label>
              <TagInput value={form.skills} onChange={(skills) => setForm({ ...form, skills })} placeholder="python, django, react…" /></div>
            <div className="grid2">
              <div><label className="f">Min experience (years)</label>
                <input type="number" min="0" step="0.5" value={form.min_experience_years} onChange={set("min_experience_years")} /></div>
              <div><label className="f">Education</label>
                <select value={form.required_education} onChange={set("required_education")}>
                  <option value="">Any</option><option value="diploma">Diploma / +2</option>
                  <option value="bachelor">Bachelor</option><option value="master">Master</option><option value="phd">PhD</option>
                </select></div>
            </div>
            <button className="primary" disabled={busy}>{busy ? "Saving…" : form.id ? "Save changes" : "Publish job"}</button>
          </form>
        </Modal>
      )}
    </div>
  );
}
