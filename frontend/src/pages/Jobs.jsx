import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { errorText } from "../api";
import { useT } from "../i18n.jsx";
import ApplyModal from "../ApplyModal.jsx";
import { Empty, MatchRing, Skeleton, StatusBadge, ago, eduText, expText, expiryText, salaryText, skillLabel, useToast } from "../ui.jsx";

const TYPES = ["full_time", "part_time", "internship", "contract"];
const SALARIES = [0, 15000, 30000, 50000, 80000];
const NONE = { q: "", location: "", skill: "", job_type: "", min_salary: "" };

export default function Jobs() {
  const { t } = useT();
  const navigate = useNavigate();
  const toast = useToast();
  const [meta, setMeta] = useState({ skills: [], locations: [], cities: [], stats: {} });
  const [filters, setFilters] = useState(NONE);
  const [jobs, setJobs] = useState(null);
  const [applyTo, setApplyTo] = useState(null);
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

  return (
    <>
      <section className="hero">
        <h1>{t("heroTitle")}</h1>
        <p>{t("heroSub")}</p>
        <form className="searchbar" onSubmit={submit}>
          <div className="field"><span>🔍</span>
            <input placeholder={t("searchPh")} value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value })} /></div>
          <div className="field"><span>📍</span>
            <input placeholder={t("cityPh")} value={filters.location} autoComplete="off"
              onChange={(e) => setFilters({ ...filters, location: e.target.value })} /></div>
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
            <article className={`card job clickable`} key={j.id}
              onClick={(e) => { if (!e.target.closest("button, a")) navigate(`/jobs/${j.id}`); }}>
              <div className="row" style={{ alignItems: "flex-start", flexWrap: "nowrap" }}>
                <div className="logo">{j.company[0]?.toUpperCase()}</div>
                <div>
                  <h3><Link to={`/jobs/${j.id}`} className="jobtitle">{j.title}</Link> <span className={`badge type-${j.job_type}`}>{t(j.job_type)}</span></h3>
                  <div className="meta"><span>🏢 {j.company}</span><span>📍 {j.location || "—"}</span>
                    <span>💰 {salaryText(j, t)}</span><span>⏱ {expText(j.min_experience_years, t)}</span>
                    {j.required_education && <span>🎓 {eduText(j.required_education, t)}</span>}</div>
                  <div className="meta"><span>🕒 {t("posted")} {ago(j.created_at, t)}</span>
                    <span className={j.days_left != null && j.days_left <= 3 ? "urgent" : ""}>⏳ {expiryText(j, t)}</span></div>
                  <div>{j.required_skills.map((s) => <span className="chip" key={s}>{skillLabel(s)}</span>)}</div>
                </div>
              </div>
              <div className="side">
                {j.resume_match != null && <div title="Match with your latest resume" style={{ textAlign: "center" }}><MatchRing value={j.resume_match} /><small>{t("yourMatch")}</small></div>}
                {j.my_application ? <StatusBadge status={j.my_application.status} />
                  : <button className="primary" onClick={() => setApplyTo(j)}>{t("applyNow")}</button>}
                <Link className="btn small" to={`/jobs/${j.id}`}>{t("viewDetails")}</Link>
              </div>
            </article>
          ))}
        </div>
      )}
      {applyTo && <ApplyModal job={applyTo} onClose={() => setApplyTo(null)} onDone={() => { setApplyTo(null); reload(); }} />}
    </>
  );
}
