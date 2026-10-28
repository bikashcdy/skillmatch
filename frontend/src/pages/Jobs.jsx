import { useEffect, useMemo, useRef, useState } from "react";
import api, { errorText } from "../api";
import { Empty, MatchRing, Modal, Skeleton, StatusBadge, skillLabel, timeAgo, useToast } from "../ui.jsx";
import { Link } from "react-router-dom";

export default function Jobs() {
  const toast = useToast();
  const [meta, setMeta] = useState({ skills: [], locations: [], cities: [], stats: {} });
  const [filters, setFilters] = useState({ q: "", location: "", skill: "" });
  const [jobs, setJobs] = useState(null);
  const [applyTo, setApplyTo] = useState(null);
  const [showAll, setShowAll] = useState(false);
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

  const submit = (e) => { e.preventDefault(); search(); };
  const pick = (skill) => {
    const f = { ...filters, skill: filters.skill === skill ? "" : skill };
    setFilters(f); search(f);
  };
  const pickCity = (city) => {
    const f = { ...filters, location: filters.location === city ? "" : city };
    setFilters(f); search(f);
  };
  const clear = () => { const f = { q: "", location: "", skill: "" }; setFilters(f); search(f); };
  const active = filters.q || filters.location || filters.skill;
  const trending = useMemo(() => meta.skills.slice(0, 7), [meta]);

  return (
    <>
      <section className="hero">
        <h1>Find a job that matches your skills</h1>
        <p>Search by what you do best and where you want to work. Your resume match shows on every job.</p>
        <form className="searchbar" onSubmit={submit}>
          <div className="field"><span>🔍</span>
            <input placeholder="Job title, skill or company" value={filters.q}
              onChange={(e) => setFilters({ ...filters, q: e.target.value })} /></div>
          <div className="field"><span>📍</span>
            <input list="locs" placeholder="City or remote" value={filters.location}
              onChange={(e) => setFilters({ ...filters, location: e.target.value })} />
            <datalist id="locs">{[...new Set([...(meta.cities || []).map((c) => c.name), ...meta.locations])].map((l) => <option key={l} value={l} />)}</datalist></div>
          <div className="field"><span>🧩</span>
            <select value={filters.skill} onChange={(e) => setFilters({ ...filters, skill: e.target.value })}>
              <option value="">All skills</option>
              {meta.skills.map((s) => <option key={s.name} value={s.name}>{skillLabel(s.name)} ({s.count})</option>)}
            </select></div>
          <button className="primary">Search Jobs</button>
        </form>
        <div className="trending">
          <b>🔥 Trending:</b>
          {trending.map((s) => (
            <button type="button" key={s.name} className={`tchip ${filters.skill === s.name ? "on" : ""}`} onClick={() => pick(s.name)}>{skillLabel(s.name)}</button>
          ))}
          {active && <button type="button" className="tchip" onClick={clear}>View All</button>}
        </div>
        <div className="trending">
          <b>📍 Popular cities:</b>
          {(showAll ? meta.cities || [] : (meta.cities || []).slice(0, 9)).map((c) => (
            <button type="button" key={c.name} className={`tchip ${filters.location === c.name ? "on" : ""}`} onClick={() => pickCity(c.name)}>
              {c.name}{c.count > 0 && <span style={{ opacity: .7 }}> · {c.count}</span>}
            </button>
          ))}
          <button type="button" className="tchip" onClick={() => setShowAll(!showAll)}>{showAll ? "Fewer ▲" : "More cities ▼"}</button>
        </div>
      </section>

      <div className="stats">
        {[["💼", meta.stats.jobs, "Jobs available"], ["🏢", meta.stats.companies, "Companies hiring"]].map(([i, n, l]) => (
          <div className="card stat" key={l}><div className="ico">{i}</div><div><b>{n ?? "–"}</b><span>{l}</span></div></div>
        ))}
      </div>

      <div className="results-head">
        <h2>{jobs ? `${jobs.length} job${jobs.length === 1 ? "" : "s"} found` : "Searching…"}</h2>
        {active && <button className="ghost" onClick={clear}>Clear filters ✕</button>}
      </div>

      {jobs === null ? <Skeleton /> : jobs.length === 0 ? (
        <Empty icon="🔎" title="No jobs match your search">Try a different skill or location, or clear the filters.</Empty>
      ) : (
        <div className="jobs">
          {jobs.map((j) => (
            <article className="card job" key={j.id}>
              <div className="row" style={{ alignItems: "flex-start", flexWrap: "nowrap" }}>
                <div className="logo">{j.company[0]?.toUpperCase()}</div>
                <div>
                  <h3>{j.title}</h3>
                  <div className="meta"><span>🏢 {j.company}</span><span>📍 {j.location || "Not specified"}</span>
                    <span>⏱ {j.min_experience_years}+ yrs</span>
                    {j.required_education && <span>🎓 {j.required_education}</span>}<span>{timeAgo(j.created_at)}</span></div>
                  <div>{j.required_skills.map((s) => <span className="chip" key={s}>{skillLabel(s)}</span>)}</div>
                </div>
              </div>
              <div className="side">
                {j.resume_match != null && <div title="Match with your latest resume" style={{ textAlign: "center" }}><MatchRing value={j.resume_match} /><small>your match</small></div>}
                {j.my_application ? <StatusBadge status={j.my_application.status} />
                  : <button className="primary" onClick={() => setApplyTo(j)}>Apply now</button>}
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
      <Modal title="Application sent 🎉" onClose={onDone}>
        <div className="stack">
          {result.map((a) => (
            <div className="card row between" key={a.id}>
              <div><b>{a.job_title}</b><div className="muted">{a.company}</div>
                <div>{a.matched_skills.map((s) => <span className="chip ok" key={s}>{s}</span>)}
                  {a.missing_skills.map((s) => <span className="chip miss" key={s}>{s}</span>)}</div>
                {a.status === "auto" && <small>Auto-applied (related job)</small>}</div>
              <MatchRing value={a.match_percentage} />
            </div>
          ))}
          <div className="row between"><Link className="btn" to="/my-applications" onClick={onDone}>View my applications</Link>
            <button className="primary" onClick={onDone}>Done</button></div>
        </div>
      </Modal>
    );
  }
  return (
    <Modal title={`Apply: ${job.title}`} onClose={onClose}>
      <form className="stack" onSubmit={submit}>
        <p className="muted">{job.company} · {job.location || "Location not specified"}</p>
        <label className={`drop ${file ? "has" : ""}`}>
          <input type="file" accept=".pdf,.docx,.txt,.png,.jpg,.jpeg" onChange={(e) => setFile(e.target.files[0] || null)} />
          {file ? <>📄 <b>{file.name}</b></> : <>📎 <b>Choose your resume</b><br /><small>PDF, DOCX, TXT or photo (leave empty to reuse your last resume)</small></>}
        </label>
        <label className="row" style={{ flexWrap: "nowrap", cursor: "pointer" }}>
          <input type="checkbox" style={{ width: 18 }} checked={auto} onChange={(e) => setAuto(e.target.checked)} />
          <span>Also apply to related jobs I match (50%+)</span>
        </label>
        <button className="primary" disabled={busy}>{busy ? "Scanning resume…" : "Submit application"}</button>
      </form>
    </Modal>
  );
}
