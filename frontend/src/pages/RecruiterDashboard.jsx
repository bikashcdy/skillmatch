import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { currentUser, errorText } from "../api";
import { Empty, Modal, Skeleton, TagInput, ago, expText, expiryText, formatDate, salaryText, skillLabel, useToast } from "../ui.jsx";
import { useT } from "../i18n.jsx";
import { jobDescriptionErrors, jobLocationErrors, jobTitleErrors } from "../validate";

const EXPERIENCE = [0, 0.5, 1, 2, 3, 4, 5, 7, 10];
const plusDays = (n) => { const d = new Date(Date.now() + n * 86400000); return d.toISOString().slice(0, 10); };
const makeEmpty = () => ({ title: "", description: "", location: "", skills: [], min_experience_years: 0, required_education: "", job_type: "full_time", salary_min: "", salary_max: "", expires_at: plusDays(30) });

export default function RecruiterDashboard() {
  const { t } = useT();
  const toast = useToast();
  const [catalog, setCatalog] = useState([]);
  const [jobs, setJobs] = useState(null);
  const [form, setForm] = useState(null);
  const [busy, setBusy] = useState(false);
  const [cities, setCities] = useState([]);
  const [errs, setErrs] = useState({});
  const FieldErr = ({ list }) => (list && list.length ? <div className="field-error">{list.map((m) => <div key={m}>• {m}</div>)}</div> : null);
  useEffect(() => { api.get("/jobs/meta/").then((x) => { setCities(x.data.cities); setCatalog(x.data.catalog || []); }); }, []);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const load = () => api.get("/recruiter/jobs/").then((r) => setJobs(r.data.results || r.data))
    .catch((e) => { setJobs([]); toast(errorText(e), "err"); });
  useEffect(() => { load(); }, []);

  async function save(e) {
    e.preventDefault();
    const found = { title: jobTitleErrors(form.title), description: jobDescriptionErrors(form.description), location: jobLocationErrors(form.location || "") };
    setErrs(found);
    if (Object.values(found).some((x) => x.length)) return toast("Please fix the highlighted fields.", "err");
    if (!form.skills.length) return toast("Add at least one required skill.", "err");
    setBusy(true);
    const body = { ...form, location: (form.location || "").trim(), required_skills: form.skills, min_experience_years: Number(form.min_experience_years) || 0,
      salary_min: form.salary_min === "" || form.salary_min == null ? null : Number(form.salary_min),
      salary_max: form.salary_max === "" || form.salary_max == null ? null : Number(form.salary_max),
      expires_at: form.expires_at || null };
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

  const approved = currentUser()?.is_approved !== false;
  const total = (jobs || []).reduce((n, j) => n + j.applicants, 0);
  return (
    <div className="stack">
      <div className="row between">
        <div><h1>{t("myJobs")}</h1><p className="muted">{jobs ? `${jobs.length} posted · ${total} applicants` : ""}</p></div>
        <button className="primary" onClick={() => { setErrs({}); setForm(makeEmpty()); }} disabled={!approved} title={approved ? "" : "Waiting for admin approval"}>＋ {t("postJob")}</button>
      </div>
      {!approved && (
        <div className="error" style={{ padding: 14 }}>
          ⏳ <b>Your recruiter account is waiting for admin approval.</b> You can look around, but you can post jobs only after it is approved. We will email you.
        </div>
      )}
      {jobs === null ? <Skeleton /> : jobs.length === 0 ? (
        <Empty icon="🧑‍💼" title="You haven't posted a job yet">Post a job with its required skills and JobMitra will rank every applicant for you.</Empty>
      ) : jobs.map((j) => (
        <div className="card" key={j.id} style={{ opacity: j.is_open ? 1 : .65 }}>
          <div className="row between">
            <div>
              <h3>{j.title} {!j.is_open && <span className="badge">{t("close")}</span>}{j.is_expired && <span className="badge rejected">{t("expiredBadge")}</span>}</h3>
              <p className="muted">📍 {j.location || "—"} · 💰 {salaryText(j, t)} · {t(j.job_type)} · ⏱ {expText(j.min_experience_years, t)} · {t("posted")} {ago(j.created_at, t)} · <b>{j.applicants}</b> applicant(s)</p>
              <p className={j.is_expired ? "urgent" : "muted"} style={{ fontSize: 13.5 }}>⏳ {j.expires_at ? `${formatDate(j.expires_at)} · ${expiryText(j, t)}` : t("noDeadline")}{j.is_expired && ` — ${t("extendHint")}`}</p>
              <div style={{ marginTop: 8 }}>{j.required_skills.map((s) => <span className="chip" key={s}>{skillLabel(s)}</span>)}</div>
            </div>
            <div className="row">
              <Link className="btn primary" to={`/recruiter/jobs/${j.id}`}>{t("rankedCands")}</Link>
              <button onClick={() => { setErrs({}); setForm({ ...j, skills: j.required_skills }); }}>{t("edit")}</button>
              <button onClick={() => toggle(j)}>{j.is_open ? t("close") : t("reopen")}</button>
              <button className="danger" onClick={() => remove(j)}>{t("del")}</button>
            </div>
          </div>
        </div>
      ))}
      {form && (
        <Modal title={form.id ? t("editJob") : t("postJob")} onClose={() => setForm(null)}>
          <form className="stack" onSubmit={save}>
            <div><label className="f">{t("jobTitle")}</label><input value={form.title} maxLength={80} onChange={(e) => { set("title")(e); setErrs({ ...errs, title: jobTitleErrors(e.target.value) }); }} /><FieldErr list={errs.title} /></div>
            <div><label className="f">{t("description")}</label><textarea value={form.description} maxLength={3000} onChange={(e) => { set("description")(e); setErrs({ ...errs, description: jobDescriptionErrors(e.target.value) }); }} /><FieldErr list={errs.description} /></div>
            <div><label className="f">{t("location")}</label>
              <select value={cities.includes(form.location) ? form.location : form.location ? "__other" : ""}
                onChange={(e) => setForm({ ...form, location: e.target.value === "__other" ? " " : e.target.value })}>
                <option value="">Select a city</option>
                {cities.map((c) => <option key={c} value={c}>{c}</option>)}
                <option value="__other">Other city…</option>
              </select>
              {!cities.includes(form.location) && form.location !== "" && (
                <input style={{ marginTop: 8 }} placeholder="Type the city or town" value={form.location.trim() === "" ? "" : form.location}
                  onChange={(e) => { setForm({ ...form, location: e.target.value || " " }); setErrs({ ...errs, location: jobLocationErrors(e.target.value) }); }} />
              )}<FieldErr list={errs.location} /></div>
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
                <select value={String(form.min_experience_years)} onChange={set("min_experience_years")}>
                  {[...new Set([...EXPERIENCE, Number(form.min_experience_years) || 0])].sort((a, b) => a - b).map((y) => (
                    <option key={y} value={y}>{expText(y, t)}</option>
                  ))}
                </select></div>
              <div><label className="f">{t("education")}</label>
                <select value={form.required_education} onChange={set("required_education")}>
                  <option value="">{t("anyEdu")}</option><option value="diploma">Diploma / +2</option>
                  <option value="bachelor">Bachelor</option><option value="master">Master</option><option value="phd">PhD</option>
                </select></div>
            </div>
            <div><label className="f">{t("expiryDate")}</label>
              <input type="date" value={form.expires_at || ""} min={plusDays(0)} onChange={set("expires_at")} /></div>
            <button className="primary" disabled={busy}>{busy ? t("saving") : form.id ? t("saveChanges") : t("publish")}</button>
          </form>
        </Modal>
      )}
    </div>
  );
}
