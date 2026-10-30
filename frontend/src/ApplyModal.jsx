import { useState } from "react";
import { Link } from "react-router-dom";
import api, { errorText } from "./api";
import { useT } from "./i18n.jsx";
import { MatchRing, Modal, skillLabel, useToast } from "./ui.jsx";

export default function ApplyModal({ job, onClose, onDone }) {
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
