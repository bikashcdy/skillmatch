import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import api, { currentUser, errorText } from "../api";
import { useT } from "../i18n.jsx";
import { Empty, MatchRing, Modal, Skeleton, StatusBadge, salaryText, skillLabel, timeAgo, useToast } from "../ui.jsx";

const TYPES = ["full_time", "part_time", "internship", "contract"];
const SALARIES = [0, 15000, 30000, 50000, 80000];
const NONE = { q: "", location: "", skill: "", job_type: "", min_salary: "", saved: "" };

export default function Jobs() {
  const { t } = useT();
  const toast = useToast();
  const [meta, setMeta] = useState({ skills: [], locations: [], cities: [], stats: {} });
  const [filters, setFilters] = useState(NONE);
  const [jobs, setJobs] = useState(null);
  const [applyTo, setApplyTo] = useState(null);
  const [showAll, setShowAll] = useState(false);
  const [alerts, setAlerts] = useState(currentUser()?.email_alerts !== false);
  const seq = useRef(0);

  const search = (f = filters) => {
    const id = ++seq.current;
    const params = Object.fromEntries(Object.entries(f).filter(([, v]) => v));
    api.get("/jobs/", { params })
      .then((r) => id === seq.current && setJobs(r.data.results || r.data))
      .catch((e) => { setJobs([]); toast(errorText(e), "err"); });
  };
  const reload = () => { search(); api.get("/jobs/meta/").then((r) => setMeta(r.data)); };
  useEffect(() => { reload(); }, []);

  const apply = (patch) => { const f = { ...filters, ...patch }; setFilters(f); search(f); };
  const submit = (e) => { e.preventDefault(); search(); };
  const clear = () => { setFilters(NONE); search(NONE); };
  const active = Object.values(filters).some(Boolean);
  const trending = useMemo(() => meta.skills.slice(0, 7), [meta]);

  async function toggleSave(job) {
    try {
      if (job.saved) await api.delete(`/jobs/${job.id}/save/`); else await api.post(`/jobs/${job.id}/save/`);
      setJobs((list) => (filters.saved && job.saved ? list.filter((j) => j.id !== job.id)
        : list.map((j) => (j.id === job.id ? { ...j, saved: !j.saved } : j))));
      toast(job.saved ? t("unsave") : t("saved") + " ★");
    } catch (e) { toast(errorText(e), "err"); }
  }
  async function toggleAlerts() {
    try {
      const { data } = await api.patch("/auth/me/", { email_alerts: !alerts });
      setAlerts(data.email_alerts);
      localStorage.setItem("user", JSON.stringify({ ...currentUser(), email_alerts: data.email_alerts }));
    } catch (e) { toast(errorText(e), "err"); }
  }

  return (
    <>
      <section className="hero">
        <h1>{t("heroTitle")}</h1>
        <p>{t("heroSub")}</p>
        <form className="searchbar" onSubmit={submit}>
          <div className="field"><span>🔍</span>
            <input placeholder={t("searchPh")} value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value })} /></div>
          <div className="field"><span>📍</span>
            <input list="locs" placeholder={t("cityPh")} value={filters.location}
              onChange={(e) => setFilters({ ...filters, location: e.target.value })} />
            <datalist id="locs">{[...new Set([...(meta.cities || []).map((c) => c.name), ...meta.locations])].map((l) => <option key={l} value={l} />)}</datalist></div>
          <div className="field"><span>🧩</span>
            <select value={filters.skill} onChange={(e) => setFilters({ ...filters, skill: e.target.value })}>
              <option value="">{t("allSkills")}</option>
              {meta.skills.map((s) => <option key={s.name} value={s.name}>{skillLabel(s.name)} ({s.count})</option>)}
            </select></div>
          <button className="primary">{t("searchBtn")}</button>
        </form>
        <div className="trending">
          <b>🔥 {t("trending")}</b>
          {trending.map((s) => (
            <button type="button" key={s.name} className={`tchip ${filters.skill === s.name ? "on" : ""}`}
              onClick={() => apply({ skill: filters.skill === s.name ? "" : s.name })}>{skillLabel(s.name)}</button>
          ))}
          {active && <button type="button" className="tchip" onClick={clear}>{t("viewAll")}</button>}
        </div>
        <div className="trending">
          <b>📍 {t("popularCities")}</b>
          {(showAll ? meta.cities || [] : (meta.cities || []).slice(0, 9)).map((c) => (
            <button type="button" key={c.name} className={`tchip ${filters.location === c.name ? "on" : ""}`}
              onClick={() => apply({ location: filters.location === c.name ? "" : c.name })}>
              {c.name}{c.count > 0 && <span style={{ opacity: .7 }}> · {c.count}</span>}
            </button>
          ))}
          <button type="button" className="tchip" onClick={() => setShowAll(!showAll)}>{showAll ? `${t("fewer")} ▲` : `${t("moreCities")} ▼`}</button>
        </div>
      </section>

      <div className="stats">
        {[["💼", meta.stats.jobs, t("jobsAvail")], ["🏢", meta.stats.companies, t("companies")]].map(([i, n, l]) => (
          <div className="card stat" key={l}><div className="ico">{i}</div><div><b>{n ?? "–"}</b><span>{l}</span></div></div>
        ))}
      </div>

      <div className="filterbar">
        <select value={filters.job_type} onChange={(e) => apply({ job_type: e.target.value })} aria-label={t("jobType")}>
          <option value="">{t("allTypes")}</option>
          {TYPES.map((x) => <option key={x} value={x}>{t(x)}</option>)}
        </select>
        <select value={filters.min_salary} onChange={(e) => apply({ min_salary: e.target.value })} aria-label="Salary">
          {SALARIES.map((s) => <option key={s} value={s || ""}>{s ? `NPR ${s.toLocaleString("en-IN")}+` : t("anySalary")}</option>)}
        </select>
        <button className={filters.saved ? "on" : ""} onClick={() => apply({ saved: filters.saved ? "" : "1" })}>★ {t("savedOnly")}</button>
        <button className={alerts ? "on" : ""} onClick={toggleAlerts}>🔔 {alerts ? t("alertsOn") : t("alertsOff")}</button>
      </div>

      <div className="results-head">
        <h2>{jobs ? (jobs.length === 1 ? t("jobFound") : t("jobsFound", { n: jobs.length })) : t("searching")}</h2>
        {active && <button className="ghost" onClick={clear}>{t("clear")} ✕</button>}
      </div>

      {jobs === null ? <Skeleton /> : jobs.length === 0 ? (
        <Empty icon="🔎" title={t("noJobs")}>{t("noJobsSub")}</Empty>
      ) : (
        <div className="jobs">
          {jobs.map((j) => (
            <article className="card job" key={j.id}>
              <div className="row" style={{ alignItems: "flex-start", flexWrap: "nowrap" }}>
                <div className="logo">{j.company[0]?.toUpperCase()}</div>
                <div>
                  <h3>{j.title} <span className={`badge type-${j.job_type}`}>{t(j.job_type)}</span></h3>
                  <div className="meta"><span>🏢 {j.company}</span><span>📍 {j.location || "—"}</span>
                    <span>💰 {salaryText(j, t)}</span><span>⏱ {j.min_experience_years}+ yrs</span>
                    {j.required_education && <span>🎓 {j.required_education}</span>}<span>{timeAgo(j.created_at)}</span></div>
                  <div>{j.required_skills.map((s) => <span className="chip" key={s}>{skillLabel(s)}</span>)}</div>
                </div>
              </div>
              <div className="side">
                <button className={`bookmark ${j.saved ? "on" : ""}`} title={j.saved ? t("unsave") : t("save")} onClick={() => toggleSave(j)}>{j.saved ? "★" : "☆"}</button>
                {j.resume_match != null && <div title="Match with your latest resume" style={{ textAlign: "center" }}><MatchRing value={j.resume_match} /><small>{t("yourMatch")}</small></div>}
                {j.my_application ? <StatusBadge status={j.my_application.status} />
                  : <button className="primary" onClick={() => setApplyTo(j)}>{t("applyNow")}</button>}
              </div>
            </article>
          ))}
        </div>
      )}
      {applyTo && <ApplyModal job={applyTo} onClose={() => setApplyTo(null)} onDone={() => { setApplyTo(null); reload(); }} />}
    </>
  );
}

function ApplyModal({ job, onClose, onDone }) {
  const { t } = useT();
  const toast = useToast();
  const [file, setFile] = useState(null);
  const [auto, setAuto] = useState(true);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  async function submit(e) {
    e.preventDefault();
    const fd = new FormData();
    if (file) fd.append("resume", file);
    fd.append("auto_apply_related", auto);
    setBusy(true);
    try {
      const { data } = await api.post(`/jobs/${job.id}/apply/`, fd);
      setResult(data);
    } catch (err) {
      toast(errorText(err, "Could not apply."), "err");
    }
    setBusy(false);
  }

  if (result) {
    return (
      <Modal title={t("sent")} onClose={onDone}>
        <div className="stack">
          {result.map((a) => (
            <div className="card row between" key={a.id}>
              <div><b>{a.job_title}</b><div className="muted">{a.company}</div>
                <div>{a.matched_skills.map((s) => <span className="chip ok" key={s}>{skillLabel(s)}</span>)}
                  {a.missing_skills.map((s) => <span className="chip miss" key={s}>{skillLabel(s)}</span>)}</div>
                {a.status === "auto" && <small>{t("statusAuto")}</small>}</div>
              <MatchRing value={a.match_percentage} />
            </div>
          ))}
          <div className="row between"><Link className="btn" to="/my-applications" onClick={onDone}>{t("viewMyApps")}</Link>
            <button className="primary" onClick={onDone}>{t("done")}</button></div>
        </div>
      </Modal>
    );
  }
  return (
    <Modal title={`${t("applyTo")}: ${job.title}`} onClose={onClose}>
      <form className="stack" onSubmit={submit}>
        <p className="muted">{job.company} · {job.location || "—"}</p>
        <label className={`drop ${file ? "has" : ""}`}>
          <input type="file" accept=".pdf,.docx,.txt,.png,.jpg,.jpeg" onChange={(e) => setFile(e.target.files[0] || null)} />
          {file ? <>📄 <b>{file.name}</b></> : <>📎 <b>{t("chooseResume")}</b><br /><small>{t("resumeHint")}</small></>}
        </label>
        <label className="row" style={{ flexWrap: "nowrap", cursor: "pointer" }}>
          <input type="checkbox" style={{ width: 18 }} checked={auto} onChange={(e) => setAuto(e.target.checked)} />
          <span>{t("alsoApply")}</span>
        </label>
        <button className="primary" disabled={busy}>{busy ? t("scanning") : t("submit")}</button>
      </form>
    </Modal>
  );
}
