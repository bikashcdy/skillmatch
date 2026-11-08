import { useEffect, useState } from "react";
import api, { errorText } from "../api";
import { Skeleton, skillLabel, useToast } from "../ui.jsx";

const NAMES = { skill: "Skills", text: "Text fit", experience: "Experience", education: "Education", preference: "Preferences" };
const pct = (v) => (v == null ? "—" : `${Math.round(v * 100)}%`);

function Weights({ w }) {
  return <span>{Object.keys(NAMES).map((k) => <span className="chip" key={k}>{NAMES[k]} {Math.round((w?.[k] ?? 0) * 100)}%</span>)}</span>;
}

/** Admin tab: matching weights, expert ratings, grid search and the skill-demand report. */
export default function AdminMatching() {
  const toast = useToast();
  const [d, setD] = useState(null);
  const [demand, setDemand] = useState(null);
  const [res, setRes] = useState(null);
  const [form, setForm] = useState({ resume: "", job: "", rating: 3, split: "tune" });
  const [busy, setBusy] = useState(false);

  const load = () => {
    api.get("/admin/weights/").then((r) => setD(r.data)).catch((e) => toast(errorText(e), "err"));
    api.get("/admin/analytics/skill-demand/").then((r) => setDemand(r.data)).catch(() => {});
  };
  useEffect(() => { load(); }, []);
  const run = async (fn, ok) => { setBusy(true); try { const r = await fn(); if (ok) toast(typeof ok === "function" ? ok(r) : ok); load(); return r; } catch (e) { toast(errorText(e), "err"); } finally { setBusy(false); } };

  if (!d) return <Skeleton n={3} />;
  const ev = d.evaluation;
  const rate = (e) => { e.preventDefault(); if (!form.resume || !form.job) return toast("Choose a resume and a job.", "err"); run(() => api.post("/admin/ratings/", form), "Rating saved"); };
  const tune = async () => { const r = await run(() => api.post("/admin/weights/tune/"), "Grid search finished"); if (r) setRes(r.data); };

  return (
    <div className="stack">
      <section className="card">
        <h2>Matching weights</h2>
        <p className="muted">Final score = 100 × (Skills + Text + Experience + Education + Preferences). A must-have skill that is completely missing caps the score at 60%.</p>
        <p style={{ marginTop: 8 }}><b>Default:</b> <Weights w={d.defaults} /></p>
        <p><b>Live now{d.active_version ? ` (version ${d.active_version})` : " (default)"}:</b> <Weights w={d.active} /></p>
        {d.active_version > 0 && <button disabled={busy} onClick={() => run(() => api.post("/admin/weights/reset/"), "Back to default weights")}>Use default weights</button>}
      </section>

      <section className="card">
        <h2>Expert ratings</h2>
        <p className="muted">Grid search needs examples of “this job is a good / bad fit for this resume” (0 = no fit … 3 = perfect). Rate at least 2 jobs per resume. Real recruiter decisions can be imported, but they are biased by the engine’s own ranking, so add some manual ratings too.</p>
        <p style={{ margin: "8px 0" }}>Tuning set: <b>{d.counts.tune}</b> · Test set: <b>{d.counts.test}</b></p>
        <form className="row" onSubmit={rate}>
          <select style={{ width: 210 }} value={form.resume} onChange={(e) => setForm({ ...form, resume: e.target.value })}><option value="">Resume…</option>{d.resumes.map((r) => <option key={r.id} value={r.id}>{r.label}</option>)}</select>
          <select style={{ width: 230 }} value={form.job} onChange={(e) => setForm({ ...form, job: e.target.value })}><option value="">Job…</option>{d.jobs.map((j) => <option key={j.id} value={j.id}>{j.label}</option>)}</select>
          <select style={{ width: 120 }} value={form.rating} onChange={(e) => setForm({ ...form, rating: Number(e.target.value) })}>{[0, 1, 2, 3].map((n) => <option key={n} value={n}>Rating {n}</option>)}</select>
          <select style={{ width: 110 }} value={form.split} onChange={(e) => setForm({ ...form, split: e.target.value })}><option value="tune">Tuning</option><option value="test">Test</option></select>
          <button className="primary" disabled={busy}>Save rating</button>
        </form>
        <div className="row" style={{ margin: "12px 0" }}>
          <button disabled={busy} onClick={() => run(() => api.post("/admin/ratings/import-decisions/"), (r) => `${r.data.created} rating(s) imported from recruiter decisions`)}>Import recruiter decisions</button>
          <button className="primary" disabled={busy} onClick={tune}>Run grid search</button>
        </div>
        {d.ratings.length > 0 && (
          <div className="tablewrap" style={{ maxHeight: 260, overflow: "auto" }}>
            <table><thead><tr><th>Candidate</th><th>Job</th><th>Rating</th><th>Set</th><th /></tr></thead>
              <tbody>{d.ratings.map((r) => (
                <tr key={r.id}><td>{r.candidate}</td><td>{r.job_title}</td><td>{r.rating}</td><td>{r.split}</td>
                  <td><button className="danger" onClick={() => run(() => api.delete(`/admin/ratings/${r.id}/`))}>✕</button></td></tr>
              ))}</tbody></table>
          </div>
        )}
      </section>

      {res && (
        <section className="card">
          <h2>Grid search result</h2>
          <p><b>Best weights:</b> <Weights w={res.weights} /></p>
          <p className="muted">{res.combinations_tested} combinations tried. NDCG@5 on tuning set: {res.tuning_ndcg?.toFixed(3)} (default {res.default_tuning_ndcg?.toFixed(3)}){res.test_ndcg != null && <> · on unseen test set: {res.test_ndcg.toFixed(3)} (default {res.default_test_ndcg?.toFixed(3)})</>}</p>
          {(res.warnings || []).map((w) => <div className="error" key={w} style={{ marginTop: 6 }}>⚠ {w}</div>)}
        </section>
      )}

      <section className="card">
        <h2>Saved configurations</h2>
        {d.configs.length === 0 ? <p className="muted">None yet. Run the grid search first.</p> : d.configs.map((c) => (
          <div className="row between resume-row" key={c.id}>
            <div><b>Version {c.version}</b> {c.is_active && <span className="badge selected">Live</span>}<br /><Weights w={c.weights} /><br /><small>Tuning NDCG {c.tuning_ndcg?.toFixed(3)}{c.test_ndcg != null ? ` · Test NDCG ${c.test_ndcg.toFixed(3)}` : ""}</small></div>
            {!c.is_active && <button className="primary" disabled={busy} onClick={() => run(() => api.post(`/admin/weights/${c.id}/activate/`), `Version ${c.version} is live`)}>Make live</button>}
          </div>
        ))}
      </section>

      {ev && (
        <section className="card">
          <h2>How good is the ranking now?</h2>
          <p className="muted">{ev.queries} ranked list(s), {ev.pairs} rated pair(s).</p>
          <div className="row" style={{ marginTop: 8 }}>
            {[["Precision@5", pct(ev.precision_at_5)], ["NDCG@5", ev.ndcg_at_5?.toFixed(3)], ["Spearman", ev.spearman?.toFixed(3)], ["Cohen’s kappa", ev.cohens_kappa?.toFixed(3)]].map(([k, v]) => (
              <div className="card stat" key={k}><div><b>{v ?? "—"}</b><span>{k}</span></div></div>
            ))}
          </div>
        </section>
      )}

      {demand && (
        <section className="card">
          <h2>Skill demand</h2>
          <p className="muted">{demand.open_jobs} open job(s), {demand.candidates} candidate(s), average match {demand.average_match}%, {demand.knockout_rate}% of applications hit the must-have cap.</p>
          <div className="tablewrap"><table><thead><tr><th>Skill</th><th>Jobs asking</th><th>Candidates having</th><th>Shortage</th></tr></thead>
            <tbody>{demand.top_demand.map((s) => <tr key={s.skill}><td>{skillLabel(s.skill)}</td><td>{s.jobs}</td><td>{s.candidates}</td><td>{s.shortage}</td></tr>)}</tbody></table></div>
        </section>
      )}
    </div>
  );
}
