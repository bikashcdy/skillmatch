import { useEffect, useState } from "react";
import api, { errorText } from "./api";
import { Bar, TagInput, skillLabel, useToast } from "./ui.jsx";

const EDUCATION = [
  ["none", "Not mentioned"], ["secondary", "Secondary (SLC / SEE)"], ["diploma", "Higher secondary (+2) / Diploma"],
  ["bachelor", "Bachelor"], ["master", "Master"], ["phd", "Doctorate"],
];

/** Tells the candidate whether photos / scanned PDFs can be read on this server. Shows nothing when OCR works. */
export function OcrNotice() {
  const [s, setS] = useState(null);
  useEffect(() => { api.get("/resume/ocr/").then((r) => setS(r.data)).catch(() => {}); }, []);
  if (!s || s.available) return null;
  return <p className="field-error">Photos and scanned PDFs cannot be read on this server yet (OCR is not installed). Text PDFs, DOCX and TXT work, or you can type your details.</p>;
}

/** The candidate checks what the scanner found, fixes it, and confirms. Also used to type details by hand. */
export function ResumeReview({ resume, manual = false, onDone, onCancel }) {
  const toast = useToast();
  const [catalog, setCatalog] = useState([]);
  const [skills, setSkills] = useState(resume?.extracted_skills || []);
  const [years, setYears] = useState(resume?.experience_years ?? 0);
  const [edu, setEdu] = useState(resume?.education_level || "none");
  const [projects, setProjects] = useState((resume?.projects || []).join("\n"));
  const [certs, setCerts] = useState((resume?.certifications || []).join("\n"));
  const [errs, setErrs] = useState({});
  const [busy, setBusy] = useState(false);
  useEffect(() => { api.get("/jobs/meta/").then((r) => setCatalog((r.data.catalog || []).map(skillLabel))).catch(() => {}); }, []);

  const lines = (text) => text.split("\n").map((x) => x.trim()).filter(Boolean);

  async function confirm(e) {
    e.preventDefault();
    const found = {};
    if (!skills.length) found.skills = ["Add at least one skill."];
    const y = Number(years);
    if (years === "" || Number.isNaN(y) || y < 0 || y > 60) found.experience_years = ["Enter years between 0 and 60."];
    setErrs(found);
    if (Object.keys(found).length) return;
    setBusy(true);
    const body = { skills, experience_years: y, education_level: edu, projects: lines(projects), certifications: lines(certs) };
    try {
      const { data } = manual || !resume?.id ? await api.post("/resume/manual/", body) : await api.post(`/resumes/${resume.id}/confirm/`, body);
      toast("Resume details saved");
      onDone(data);
    } catch (ex) {
      const d = ex.response?.data;
      if (d && typeof d === "object" && !d.detail) setErrs(Object.fromEntries(Object.entries(d).map(([k, v]) => [k, [].concat(v)])));
      else toast(errorText(ex), "err");
    }
    setBusy(false);
  }

  return (
    <form className="stack" onSubmit={confirm} noValidate>
      <p className="muted">
        {manual || !resume?.id
          ? "We could not read a file, so type your details here. This is what recruiters will be matched against."
          : <>We scanned <b>{resume.filename}</b>. Check the details below, fix anything that is wrong, then confirm. Only confirmed details are used for matching.</>}
      </p>
      <div>
        <label className="f">Skills</label>
        <TagInput suggestions={catalog} value={skills.map(skillLabel)} onChange={(v) => setSkills(v.map((s) => s.toLowerCase()))} placeholder="python, react, sql…" />
        {errs.skills && <p className="field-error">{errs.skills[0]}</p>}
      </div>
      <div className="grid2">
        <div>
          <label className="f">Years of experience</label>
          <input type="number" min="0" max="60" step="0.5" value={years} onChange={(e) => setYears(e.target.value)} className={errs.experience_years ? "bad" : ""} />
          {errs.experience_years && <p className="field-error">{errs.experience_years[0]}</p>}
        </div>
        <div>
          <label className="f">Highest education</label>
          <select value={edu} onChange={(e) => setEdu(e.target.value)}>{EDUCATION.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
          {errs.education_level && <p className="field-error">{errs.education_level[0]}</p>}
        </div>
      </div>
      <div><label className="f">Projects (one per line)</label><textarea style={{ minHeight: 70 }} value={projects} onChange={(e) => setProjects(e.target.value)} /></div>
      <div><label className="f">Certifications (one per line)</label><textarea style={{ minHeight: 60 }} value={certs} onChange={(e) => setCerts(e.target.value)} /></div>
      <div className="row between">
        {onCancel ? <button type="button" onClick={onCancel}>Cancel</button> : <span />}
        <button className="primary" disabled={busy}>{busy ? "Saving…" : "Confirm details"}</button>
      </div>
    </form>
  );
}

/** Why a job got its score: the five parts, partial skills, the skill gap and the knock-out warning. */
export function ScoreBreakdown({ a }) {
  const row = (label, v) => (v == null ? <div className="bar" key={label}><span>{label}</span><span className="muted">not set</span><b /></div> : <Bar key={label} label={label} value={v} />);
  return (
    <div className="stack" style={{ gap: 8 }}>
      {a.knockout && (
        <div className="error">
          ⚠ A must-have skill is missing{a.missing_must_have?.length ? <>: <b>{a.missing_must_have.map(skillLabel).join(", ")}</b></> : ""}. The score is capped at 60%.
        </div>
      )}
      {row("Skills", a.skill_score)}
      {row("Text fit", a.text_score)}
      {row("Experience", a.experience_score)}
      {row("Education", a.education_score)}
      {row("Preferences", a.preference_score)}
      <div>
        {a.matched_skills.map((s) => <span className="chip ok" key={s}>✓ {skillLabel(s)}</span>)}
        {(a.partial_skills || []).map((s) => <span className="chip part" key={s} title="A related skill gives half credit">~ {skillLabel(s)}</span>)}
        {a.missing_skills.map((s) => <span className="chip miss" key={s}>✗ {skillLabel(s)}</span>)}
      </div>
      {a.skill_gap > 0 && <small>Skill gap: {a.skill_gap}% of the job's skills are completely missing. “~” skills are related and count half.</small>}
    </div>
  );
}
