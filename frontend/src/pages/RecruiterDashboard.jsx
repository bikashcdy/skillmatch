import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorText } from "../api";
import { Empty, Modal, Skeleton, TagInput, salaryText, skillLabel, timeAgo, useToast } from "../ui.jsx";
import { useT } from "../i18n.jsx";

const empty = { title: "", description: "", location: "", skills: [], min_experience_years: 0, required_education: "", job_type: "full_time", salary_min: "", salary_max: "" };

export default function RecruiterDashboard() {
  const { t } = useT();
  const toast = useToast();
  const [catalog, setCatalog] = useState([]);
  const [jobs, setJobs] = useState(null);
  const [form, setForm] = useState(null);
  const [busy, setBusy] = useState(false);
  const [cities, setCities] = useState([]);
  useEffect(() => { api.get("/jobs/meta/").then((x) => { setCities(x.data.cities.map((c) => c.name)); setCatalog(x.data.catalog || []); }); }, []);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const load = () => api.get("/recruiter/jobs/").then((r) => setJobs(r.data.results || r.data))
    .catch((e) => { setJobs([]); toast(errorText(e), "err"); });
  useEffect(() => { load(); }, []);

  async function save(e) {
    e.preventDefault();
    if (!form.skills.length) return toast("Add at least one required skill.", "err");
    setBusy(true);
    const body = { ...form, location: (form.location || "").trim(), required_skills: form.skills, min_experience_years: Number(form.min_experience_years) || 0,
      salary_min: form.salary_min === "" || form.salary_min == null ? null : Number(form.salary_min),
      salary_max: form.salary_max === "" || form.salary_max == null ? null : Number(form.salary_max) };
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
        <div><h1>{t("myJobs")}</h1><p className="muted">{jobs ? `${jobs.length} posted · ${total} applicants` : ""}</p></div>
        <button className="primary" onClick={() => setForm(empty)}>＋ {t("postJob")}</button>
      </div>
      {jobs === null ? <Skeleton /> : jobs.length === 0 ? (
        <Empty icon="🧑‍💼" title="You haven't posted a job yet">Post a job with its required skills and JobMitra will rank every applicant for you.</Empty>
      ) : jobs.map((j) => (
        <div className="card" key={j.id} style={{ opacity: j.is_open ? 1 : .65 }}>
          <div className="row between">
            <div>
              <h3>{j.title} {!j.is_open && <span className="badge">{t("close")}</span>}</h3>
              <p className="muted">📍 {j.location || "—"} · 💰 {salaryText(j, t)} · {t(j.job_type)} · {j.min_experience_years}+ yrs · posted {timeAgo(j.created_at)} · <b>{j.applicants}</b> applicant(s)</p>
              <div style={{ marginTop: 8 }}>{j.required_skills.map((s) => <span className="chip" key={s}>{skillLabel(s)}</span>)}</div>
            </div>
            <div className="row">
              <Link className="btn primary" to={`/recruiter/jobs/${j.id}`}>{t("rankedCands")}</Link>
              <button onClick={() => setForm({ ...j, skills: j.required_skills })}>{t("edit")}</button>
              <button onClick={() => toggle(j)}>{j.is_open ? t("close") : t("reopen")}</button>
              <button className="danger" onClick={() => remove(j)}>{t("del")}</button>
            </div>
          </div>
        </div>
      ))}
      {form && (
        <Modal title={form.id ? t("editJob") : t("postJob")} onClose={() => setForm(null)}>
          <form className="stack" onSubmit={save}>
            <div><label className="f">{t("jobTitle")}</label><input value={form.title} onChange={set("title")} required /></div>
            <div><label className="f">{t("description")}</label><textarea value={form.description} onChange={set("description")} required /></div>
            <div><label className="f">{t("location")}</label>
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
            <div><label className="f">{t("reqSkills")}</label>
              <TagInput suggestions={catalog.map(skillLabel)} value={form.skills} onChange={(skills) => setForm({ ...form, skills })} placeholder="python, django, react…" /></div>
            <div className="grid2">
              <div><label className="f">{t("jobType")}</label>
                <select value={form.job_type} onChange={set("job_type")}>
                  {["full_time", "part_time", "internship", "contract"].map((x) => <option key={x} value={x}>{t(x)}</option>)}
                </select></div>
              <div><label className="f">&nbsp;</label><p className="muted" style={{ fontSize: 13, paddingTop: 8 }}>Leave salary empty if negotiable.</p></div>
            </div>
            <div className="grid2">
              <div><label className="f">{t("salaryMin")}</label><input type="number" min="0" step="1000" value={form.salary_min ?? ""} onChange={set("salary_min")} /></div>
              <div><label className="f">{t("salaryMax")}</label><input type="number" min="0" step="1000" value={form.salary_max ?? ""} onChange={set("salary_max")} /></div>
            </div>
            <div className="grid2">
              <div><label className="f">{t("minExp")}</label>
                <input type="number" min="0" step="0.5" value={form.min_experience_years} onChange={set("min_experience_years")} /></div>
              <div><label className="f">{t("education")}</label>
                <select value={form.required_education} onChange={set("required_education")}>
                  <option value="">{t("anyEdu")}</option><option value="diploma">Diploma / +2</option>
                  <option value="bachelor">Bachelor</option><option value="master">Master</option><option value="phd">PhD</option>
                </select></div>
            </div>
            <button className="primary" disabled={busy}>{busy ? t("saving") : form.id ? t("saveChanges") : t("publish")}</button>
          </form>
        </Modal>
      )}
    </div>
  );
}
