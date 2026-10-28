import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorText } from "../api";
import { Empty, MatchRing, Skeleton, skillLabel, useToast } from "../ui.jsx";

export default function Recommendations() {
  const toast = useToast();
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const fileRef = useRef();

  const load = () => api.get("/recommendations/").then((r) => setData(r.data))
    .catch((e) => { setData({ has_resume: false }); toast(errorText(e), "err"); });
  useEffect(() => { load(); }, []);

  async function upload(file) {
    if (!file) return;
    const fd = new FormData();
    fd.append("resume", file);
    setBusy(true);
    try { await api.post("/resume/", fd); toast("Resume scanned"); await load(); }
    catch (e) { toast(errorText(e, "Could not scan this resume."), "err"); }
    setBusy(false);
    if (fileRef.current) fileRef.current.value = "";
  }

  const Upload = ({ label }) => (
    <label className={`btn ${data?.has_resume ? "" : "primary"}`} style={{ cursor: "pointer" }}>
      {busy ? "Scanning…" : label}
      <input ref={fileRef} type="file" hidden accept=".pdf,.docx,.txt,.png,.jpg,.jpeg" disabled={busy}
        onChange={(e) => upload(e.target.files[0])} />
    </label>
  );

  if (!data) return <Skeleton n={4} />;
  if (!data.has_resume) {
    return (
      <Empty icon="📄" title="Scan your resume to get your personal plan">
        Upload your resume (PDF, DOCX, TXT or a photo). We will show which skills to learn, where to learn them, and how much each one raises your match.
        <div style={{ marginTop: 16 }}><Upload label="Upload & scan resume" /></div>
      </Empty>
    );
  }

  const r = data.resume;
  return (
    <div className="stack">
      <div className="row between">
        <div><h1>Your career plan</h1><p className="muted">Based on your latest resume and {data.jobs_count} open jobs</p></div>
        <Upload label="Upload a newer resume" />
      </div>

      <section className="card plan-hero">
        <div>
          <small>RESUME SCAN · {r.filename}</small>
          <h2 style={{ margin: "4px 0 10px" }}>{r.experience_years} yr experience · {r.education_level} education</h2>
          <div>{data.skills_have.length ? data.skills_have.map((s) => <span className="chip ok" key={s}>✓ {s}</span>)
            : <span className="muted">No known skills detected yet.</span>}</div>
        </div>
        {data.focus.length > 0 && (
          <div className="boost">
            <div className="boost-nums">
              <div><b>{data.avg_now}%</b><small>average match now</small></div>
              <span>→</span>
              <div className="after"><b>{data.avg_after}%</b><small>after learning {data.focus.length} skills</small></div>
            </div>
            <p className="muted">Focus on <b>{data.focus.map(skillLabel).join(", ")}</b> first. About {data.weeks_total} weeks of steady study.</p>
          </div>
        )}
      </section>

      <h2>Skills to learn, in order of impact</h2>
      {data.skill_gaps.length === 0 ? (
        <Empty icon="🎉" title="No skill gaps found">Your resume already covers every skill the open jobs ask for.</Empty>
      ) : data.skill_gaps.map((g) => (
        <article className="card gap" key={g.skill}>
          <div className="gap-rank">{g.rank}</div>
          <div className="gap-body">
            <div className="row between" style={{ alignItems: "flex-start" }}>
              <div>
                <h3>{skillLabel(g.skill)}</h3>
                <p className="muted">{g.why}</p>
              </div>
              <div className="gain">+{g.avg_gain}%<small>avg match boost</small></div>
            </div>
            <p style={{ margin: "8px 0" }}>
              Needed by <b>{g.jobs_needing}</b> job{g.jobs_needing > 1 ? "s" : ""} ({g.job_titles.join(", ")}) · about <b>{g.weeks} weeks</b> to get started
            </p>
            {g.unlocks.length > 0 && <p className="success-text" style={{ fontSize: 14 }}>Unlocks 75%+ match for: {g.unlocks.join(", ")}</p>}
            <div className="res">
              {g.resources.map((l) => (
                <a key={l.url} href={l.url} target="_blank" rel="noreferrer">📚 {l.label} <span>↗</span></a>
              ))}
            </div>
          </div>
        </article>
      ))}

      <h2>Jobs closest to you</h2>
      <div className="jobs">
        {data.best_jobs.map((j) => (
          <div className="card row between" key={j.id}>
            <div>
              <h3>{j.title}</h3>
              <p className="muted">{j.company} · 📍 {j.location || "—"}</p>
              <div style={{ marginTop: 6 }}>
                {j.matched_skills.map((s) => <span className="chip ok" key={s}>✓ {s}</span>)}
                {j.missing_skills.map((s) => <span className="chip miss" key={s}>✗ {s}</span>)}
              </div>
            </div>
            <div className="row" style={{ flexWrap: "nowrap" }}>
              <div style={{ textAlign: "center" }}><MatchRing value={j.match} /><small>now</small></div>
              {j.match_after > j.match && <>
                <span className="muted">→</span>
                <div style={{ textAlign: "center" }}><MatchRing value={j.match_after} /><small>after plan</small></div>
              </>}
            </div>
          </div>
        ))}
      </div>

      {data.tips.length > 0 && (<>
        <h2>Other things to improve</h2>
        <div className="grid2">
          {data.tips.map((t) => (
            <div className="card" key={t.area}><span className="badge auto">{t.area}</span><p style={{ marginTop: 8 }}>{t.text}</p></div>
          ))}
        </div>
      </>)}

      <h2>How to actually learn</h2>
      <div className="card"><ul className="ideas">{data.ideas.map((i) => <li key={i}>{i}</li>)}</ul></div>
      <p className="muted" style={{ textAlign: "center" }}>
        Ready? <Link to="/jobs" style={{ color: "var(--accent)", fontWeight: 600 }}>Browse jobs</Link> and apply.
        Percentages are estimates from our scanner, not a guarantee.
      </p>
    </div>
  );
}
