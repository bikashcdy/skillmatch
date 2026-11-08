import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorText } from "../api";
import { Empty, MatchRing, Modal, Skeleton, skillLabel, useToast } from "../ui.jsx";
import { useT } from "../i18n.jsx";
import { OcrNotice, ResumeReview } from "../ui_resume.jsx";

export default function Recommendations() {
  const { t } = useT();
  const toast = useToast();
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const fileRef = useRef();
  const [review, setReview] = useState(null);   // scanned resume waiting for the candidate to confirm
  const [sim, setSim] = useState({ picked: [], result: null, busy: false });

  const load = () => api.get("/recommendations/").then((r) => setData(r.data))
    .catch((e) => { setData({ has_resume: false }); toast(errorText(e), "err"); });
  useEffect(() => { load(); }, []);

  async function upload(file) {
    if (!file) return;
    const fd = new FormData();
    fd.append("resume", file);
    setBusy(true);
    try { const { data: d } = await api.post("/resume/", fd); setReview({ resume: d, manual: false }); }
    catch (e) {
      if (e.response?.data?.manual_entry) setReview({ resume: null, manual: true });
      toast(errorText(e, "Could not scan this resume."), "err");
    }
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

  const reviewModal = review && (
    <Modal title="Check your resume details" onClose={() => setReview(null)}>
      <ResumeReview resume={review.resume} manual={review.manual} onCancel={() => setReview(null)}
        onDone={async () => { setReview(null); await load(); }} />
    </Modal>
  );

  async function simulate(picked) {
    setSim({ picked, result: null, busy: !!picked.length });
    if (!picked.length) return;
    try { const { data: d } = await api.post("/recommendations/what-if/", { skills: picked }); setSim({ picked, result: d, busy: false }); }
    catch (e) { toast(errorText(e), "err"); setSim({ picked, result: null, busy: false }); }
  }
  const togglePick = (skill) => simulate(sim.picked.includes(skill) ? sim.picked.filter((x) => x !== skill) : [...sim.picked, skill]);

  if (!data) return <Skeleton n={4} />;
  if (!data.has_resume) {
    return (<>
      <Empty icon="📄" title={t("scanFirst")}>
        Upload your resume (PDF, DOCX, TXT or a photo). We will show which skills to learn, where to learn them, and how much each one raises your match.
        <div style={{ marginTop: 16 }}><Upload label={t("uploadScan")} /><OcrNotice /></div>
        <p style={{ marginTop: 10 }}><button className="ghost" onClick={() => setReview({ resume: null, manual: true })}>or type your details instead</button></p>
      </Empty>
      {reviewModal}
    </>);
  }

  const r = data.resume;
  return (
    <div className="stack">
      {reviewModal}
      <div className="row between">
        <div><h1>{t("planTitle")}</h1><p className="muted">{t("planSub", { n: data.jobs_count })}</p></div>
        <Upload label={t("uploadNewer")} />
      </div>

      <section className="card plan-hero">
        <div>
          <small>RESUME · {r.filename || "typed details"}</small>
          <h2 style={{ margin: "4px 0 10px" }}>{r.experience_years} yr experience · {r.education_level} education</h2>
          <div>{data.skills_have.length ? data.skills_have.map((s) => <span className="chip ok" key={s}>✓ {s}</span>)
            : <span className="muted">No known skills detected yet.</span>}</div>
        </div>
        {data.focus.length > 0 && (
          <div className="boost">
            <div className="boost-nums">
              <div><b>{data.avg_now}%</b><small>{t("avgNow")}</small></div>
              <span>→</span>
              <div className="after"><b>{data.avg_after}%</b><small>{t("avgAfter", { n: data.focus.length })}</small></div>
            </div>
            <p className="muted">Focus on <b>{data.focus.map(skillLabel).join(", ")}</b> first. About {data.weeks_total} weeks of steady study.</p>
          </div>
        )}
      </section>

      {data.health && (
        <section className="card health">
          <div className="health-head">
            <MatchRing value={data.health.score} size={84} />
            <div><h2>{t("resumeCheck")}</h2><p className="muted">{t("resumeScore")}: <b>{data.health.score}/100</b> · {t("fixThese")}</p></div>
          </div>
          <ul className="checklist">
            {data.health.checks.map((c) => (
              <li key={c.key} className={c.ok ? "ok" : "bad"}>
                <span>{c.ok ? "✓" : "✗"}</span>
                <div><b>{c.label}</b>{!c.ok && <p>{c.tip}</p>}</div>
              </li>
            ))}
          </ul>
        </section>
      )}

      <h2>{t("skillsToLearn")}</h2>
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
              <div className="gain">+{g.avg_gain}%<small>{t("boost")}</small></div>
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

      {data.learning_path?.length > 0 && (<>
        <h2>Your learning order</h2>
        <div className="card">
          <p className="muted" style={{ marginBottom: 10 }}>Follow this order: each skill builds on the ones before it.</p>
          <ol className="ideas">
            {data.learning_path.map((p) => (
              <li key={p.skill}><b>{skillLabel(p.skill)}</b> · about {p.weeks} week{p.weeks > 1 ? "s" : ""}
                {!p.is_gap && <span className="badge" style={{ marginLeft: 8 }}>prerequisite</span>}
                {p.needed_for.length > 0 && <small> needed for {p.needed_for.map(skillLabel).join(", ")}</small>}</li>
            ))}
          </ol>
        </div>
      </>)}

      {data.skill_gaps.length > 0 && (<>
        <h2>What if I learn…?</h2>
        <div className="card stack">
          <p className="muted">Pick skills to see how your match scores would change. Your real profile is not changed.</p>
          <div>{data.skill_gaps.map((g) => (
            <button type="button" key={g.skill} className={`chip ${sim.picked.includes(g.skill) ? "ok" : ""}`} style={{ cursor: "pointer", border: "1px solid var(--line)" }}
              onClick={() => togglePick(g.skill)}>{sim.picked.includes(g.skill) ? "✓ " : "+ "}{skillLabel(g.skill)}</button>
          ))}</div>
          {sim.busy && <p className="muted">Calculating…</p>}
          {sim.result && (<>
            <p>Average of your top jobs: <b>{sim.result.avg_before}%</b> → <b className="success-text">{sim.result.avg_after}%</b>
              {sim.result.crossing.length > 0 && <> · reaches 75%+ for <b>{sim.result.crossing.join(", ")}</b></>}</p>
            <div className="tablewrap"><table>
              <thead><tr><th>Job</th><th>Now</th><th>After</th><th>Change</th></tr></thead>
              <tbody>{sim.result.jobs.slice(0, 6).map((j) => (
                <tr key={j.id}><td>{j.title}</td><td>{j.before}%</td><td>{j.after}%</td>
                  <td className={j.change > 0 ? "success-text" : ""}>{j.change > 0 ? "+" : ""}{j.change}%</td></tr>
              ))}</tbody>
            </table></div>
          </>)}
        </div>
      </>)}

      <h2>{t("closest")}</h2>
      <div className="jobs">
        {data.best_jobs.map((j) => (
          <div className="card row between" key={j.id}>
            <div>
              <h3>{j.title}</h3>
              <p className="muted">{j.company} · 📍 {j.location || "—"}</p>
              <div style={{ marginTop: 6 }}>
                {j.matched_skills.map((s) => <span className="chip ok" key={s}>✓ {s}</span>)}
                {(j.partial_skills || []).map((s) => <span className="chip part" key={s}>~ {s}</span>)}
                {j.missing_skills.map((s) => <span className="chip miss" key={s}>✗ {s}</span>)}
              </div>
              {j.knockout && <small className="urgent">Missing a must-have skill: score capped at 60%</small>}
            </div>
            <div className="row" style={{ flexWrap: "nowrap" }}>
              <div style={{ textAlign: "center" }}><MatchRing value={j.match} /><small>{t("now")}</small></div>
              {j.match_after > j.match && <>
                <span className="muted">→</span>
                <div style={{ textAlign: "center" }}><MatchRing value={j.match_after} /><small>{t("afterPlan")}</small></div>
              </>}
            </div>
          </div>
        ))}
      </div>

      {data.tips.length > 0 && (<>
        <h2>{t("other")}</h2>
        <div className="grid2">
          {data.tips.map((t) => (
            <div className="card" key={t.area}><span className="badge auto">{t.area}</span><p style={{ marginTop: 8 }}>{t.text}</p></div>
          ))}
        </div>
      </>)}

      <h2>{t("howLearn")}</h2>
      <div className="card"><ul className="ideas">{data.ideas.map((i) => <li key={i}>{i}</li>)}</ul></div>
      <p className="muted" style={{ textAlign: "center" }}>
        Ready? <Link to="/jobs" style={{ color: "var(--accent)", fontWeight: 600 }}>Browse jobs</Link> and apply.
        Percentages are estimates from our scanner, not a guarantee.
      </p>
    </div>
  );
}
