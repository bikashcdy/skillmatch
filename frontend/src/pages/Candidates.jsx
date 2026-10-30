import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api, { errorText, openResume } from "../api";
import { Bar, Empty, MatchRing, Modal, Skeleton, StatusBadge, skillLabel, useToast } from "../ui.jsx";
import { useT } from "../i18n.jsx";

export default function Candidates() {
  const { id } = useParams();
  const { t } = useT();
  const toast = useToast();
  const [msg, setMsg] = useState(null);
  const [apps, setApps] = useState(null);
  const [open, setOpen] = useState(null);

  const load = () => api.get(`/recruiter/jobs/${id}/candidates/`).then((r) => setApps(r.data))
    .catch((e) => { setApps([]); toast(errorText(e, "Could not load candidates."), "err"); });
  useEffect(() => { load(); }, [id]);

  async function selectBest() {
    try {
      const { data } = await api.post(`/recruiter/jobs/${id}/select-best/`);
      toast(`Selected ${data.candidate_name} (${data.match_percentage}%)`); load();
    } catch (e) { toast(errorText(e), "err"); }
  }
  async function setStatus(a, status) {
    try { await api.post(`/recruiter/applications/${a.id}/status/`, { status }); load(); }
    catch (e) { toast(errorText(e), "err"); }
  }

  async function sendNote(e) {
    e.preventDefault();
    try {
      await api.post(`/recruiter/applications/${msg.app.id}/note/`, { note: msg.text });
      toast(msg.text.trim() ? "Message sent" : "Message removed"); setMsg(null); load();
    } catch (err) { toast(errorText(err), "err"); }
  }

  return (
    <div className="stack">
      <Link to="/recruiter" className="muted">← {t("back")}</Link>
      <div className="row between">
        <div><h1>{t("rankedCands")}</h1><p className="muted">{t("highestFirst")}</p></div>
        <button className="primary" onClick={selectBest} disabled={!apps?.length}>★ {t("selectBest")}</button>
      </div>
      {apps === null ? <Skeleton /> : apps.length === 0 ? (
        <Empty icon="📭" title="No applicants yet">Candidates who apply (or are auto-matched) will appear here, ranked.</Empty>
      ) : apps.map((a, i) => (
        <div className={`card ${a.status === "selected" ? "success" : ""} ${a.status === "rejected" ? "rejected" : ""}`} key={a.id}>
          <div className="row between" style={{ flexWrap: "nowrap" }}>
            <div className="row" style={{ flexWrap: "nowrap" }}>
              <div className="logo">#{i + 1}</div>
              <div><h3>{a.candidate_name} <StatusBadge status={a.status} /></h3>
                <p className="muted">{a.candidate_email} · {a.candidate_experience} yrs · {a.candidate_education}</p></div>
            </div>
            <MatchRing value={a.match_percentage} size={72} />
          </div>
          <div style={{ marginTop: 10 }}>
            {a.matched_skills.map((s) => <span className="chip ok" key={s}>✓ {skillLabel(s)}</span>)}
            {a.missing_skills.map((s) => <span className="chip miss" key={s}>missing: {skillLabel(s)}</span>)}
          </div>
          {a.recruiter_note && <div className="note"><b>💬 {t("message")}</b><p>{a.recruiter_note}</p></div>}
          {open === a.id && (
            <div className="stack" style={{ marginTop: 12 }}>
              <Bar label="Skills" value={a.skill_score} /><Bar label="Experience" value={a.experience_score} /><Bar label="Education" value={a.education_score} />
              <div><small>Skills found in resume:</small><br />{a.candidate_skills.map((s) => <span className="chip" key={s}>{skillLabel(s)}</span>)}</div>
            </div>
          )}
          <div className="row" style={{ marginTop: 14 }}>
            <button onClick={() => setOpen(open === a.id ? null : a.id)}>{open === a.id ? t("hideDetails") : t("details")}</button>
            <button onClick={() => openResume(a.resume).catch((e) => toast(errorText(e, "Could not open the file."), "err"))}>📄 {t("resume")}</button>
            <button onClick={() => setMsg({ app: a, text: a.recruiter_note || "" })}>💬 {t("message")}</button>
            {a.status !== "selected" && <button className="primary" onClick={() => setStatus(a, "selected")}>{t("select")}</button>}
            {a.status !== "rejected" ? <button className="danger" onClick={() => setStatus(a, "rejected")}>{t("reject")}</button>
              : <button onClick={() => setStatus(a, "applied")}>{t("restore")}</button>}
          </div>
        </div>
      ))}
      {msg && (
        <Modal title={`${t("msgTitle")}: ${msg.app.candidate_name}`} onClose={() => setMsg(null)}>
          <form className="stack" onSubmit={sendNote}>
            <p className="muted">{t("msgHint")}</p>
            <textarea maxLength={500} value={msg.text} onChange={(e) => setMsg({ ...msg, text: e.target.value })} placeholder="Interview on Sunday at 11 AM, Kathmandu office." />
            <div>{["tplInterview", "tplDocs", "tplThanks"].map((k) => (
              <button type="button" className="tchip-dark" key={k} onClick={() => setMsg({ ...msg, text: t(k) })}>{t(k).slice(0, 34)}…</button>
            ))}</div>
            <button className="primary">{t("sendMsg")}</button>
          </form>
        </Modal>
      )}
    </div>
  );
}
