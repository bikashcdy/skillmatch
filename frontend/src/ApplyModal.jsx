import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorText } from "./api";
import { useT } from "./i18n.jsx";
import { MatchRing, Modal, skillLabel, useToast } from "./ui.jsx";
import { OcrNotice, ResumeReview, ScoreBreakdown } from "./ui_resume.jsx";

export default function ApplyModal({ job, onClose, onDone }) {
  const { t } = useT();
  const toast = useToast();
  const [saved, setSaved] = useState(null);      // confirmed resumes the candidate already has
  const [useSaved, setUseSaved] = useState(true);
  const [file, setFile] = useState(null);
  const [auto, setAuto] = useState(false);   // never apply to other jobs unless the candidate ticks it
  const [pick, setPick] = useState(0);         // which saved resume is selected
  const [showSkills, setShowSkills] = useState(false);
  const [busy, setBusy] = useState(false);
  const [review, setReview] = useState(null);    // {resume, manual} while the candidate checks the scan
  const [result, setResult] = useState(null);
  const [open, setOpen] = useState(null);

  useEffect(() => {
    api.get("/resumes/").then((r) => {
      const ok = r.data.filter((x) => x.confirmed);
      setSaved(ok);
      if (!ok.length) setUseSaved(false);
    }).catch(() => { setSaved([]); setUseSaved(false); });
  }, []);

  async function applyWith(resumeId) {
    setBusy(true);
    try {
      const { data } = await api.post(`/jobs/${job.id}/apply/`, { resume_id: resumeId, auto_apply_related: auto });
      setResult(data);
    } catch (err) {
      toast(errorText(err, "Could not apply."), "err");
    }
    setBusy(false);
  }

  async function submit(e) {
    e.preventDefault();
    if (useSaved && saved?.length) return applyWith(saved[pick].id);
    if (!file) return toast("Choose your resume file first.", "err");
    const fd = new FormData();
    fd.append("resume", file);
    setBusy(true);
    try {
      const { data } = await api.post("/resume/", fd);
      setReview({ resume: data, manual: false });
    } catch (err) {
      if (err.response?.data?.manual_entry) setReview({ resume: null, manual: true });
      toast(errorText(err, "Could not scan this resume."), "err");
    }
    setBusy(false);
  }

  if (review) {
    return (
      <Modal title="Check your resume details" onClose={onClose}>
        <ResumeReview resume={review.resume} manual={review.manual} onCancel={() => setReview(null)}
          onDone={(r) => { setReview(null); applyWith(r.id); }} />
      </Modal>
    );
  }

  if (result) {
    return (
      <Modal title={t("sent")} onClose={onDone}>
        <div className="stack">
          {result.map((a) => (
            <div className="card" key={a.id}>
              <div className="row between">
                <div><b>{a.job_title}</b><div className="muted">{a.company}</div>
                  {a.status === "auto" && <small>{t("statusAuto")}</small>}</div>
                <MatchRing value={a.match_percentage} />
              </div>
              <button type="button" className="ghost" style={{ padding: "4px 0" }} onClick={() => setOpen(open === a.id ? null : a.id)}>
                {open === a.id ? "Hide" : "Show"} why this score
              </button>
              {open === a.id && <ScoreBreakdown a={a} />}
              {open !== a.id && <div>{a.matched_skills.map((s) => <span className="chip ok" key={s}>{skillLabel(s)}</span>)}
                {a.missing_skills.map((s) => <span className="chip miss" key={s}>{skillLabel(s)}</span>)}</div>}
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
        {saved?.length > 0 && (
          <label className="row" style={{ flexWrap: "nowrap", cursor: "pointer" }}>
            <input type="radio" style={{ width: 18 }} checked={useSaved} onChange={() => setUseSaved(true)} />
            <span>Use my saved resume{saved.length > 1 ? "" : " "}
              {saved.length > 1
                ? <select style={{ marginLeft: 6, width: "auto" }} value={pick} onChange={(e) => setPick(Number(e.target.value))}>{saved.map((r, i) => <option key={r.id} value={i}>{r.filename || "(typed details)"}</option>)}</select>
                : <b>{saved[0].filename || "(typed details)"}</b>}
              <br /><small>{saved[pick].extracted_skills.length} skills · {saved[pick].experience_years} yr · you already confirmed these details</small></span>
          </label>
        )}
        {saved?.length > 0 && (
          <label className="row" style={{ flexWrap: "nowrap", cursor: "pointer" }}>
            <input type="radio" style={{ width: 18 }} checked={!useSaved} onChange={() => setUseSaved(false)} />
            <span>Upload a different resume</span>
          </label>
        )}
        {!useSaved && (<>
          <label className={`drop ${file ? "has" : ""}`}>
            <input type="file" accept=".pdf,.docx,.txt,.png,.jpg,.jpeg" onChange={(e) => setFile(e.target.files[0] || null)} />
            {file ? <>📄 <b>{file.name}</b></> : <>📎 <b>{t("chooseResume")}</b><br /><small>{t("resumeHint")}</small></>}
          </label>
          <OcrNotice />
        </>)}
        {useSaved && saved?.length > 0 && (
          <div>
            <button type="button" className="ghost" style={{ padding: 0 }} onClick={() => setShowSkills(!showSkills)}>{showSkills ? "Hide" : "Check"} the skills that will be used</button>
            {showSkills && <div style={{ marginTop: 6 }}>{saved[pick].extracted_skills.map((s) => <span className="chip" key={s}>{skillLabel(s)}</span>)}
              <small className="muted" style={{ display: "block", marginTop: 6 }}>Wrong or missing? Close this window, open Profile and press Review on the resume.</small></div>}
          </div>
        )}
        <label className="row" style={{ flexWrap: "nowrap", cursor: "pointer" }}>
          <input type="checkbox" style={{ width: 18 }} checked={auto} onChange={(e) => setAuto(e.target.checked)} />
          <span>{t("alsoApply")}</span>
        </label>
        <button className="primary wide" disabled={busy || saved === null}>{busy ? t("scanning") : useSaved ? t("submit") : "Scan resume"}</button>
      </form>
    </Modal>
  );
}