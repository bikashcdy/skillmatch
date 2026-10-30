import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorText, openResume } from "../api";
import { useT } from "../i18n.jsx";
import { Bar, Empty, MatchRing, Skeleton, StatusBadge, skillLabel, ago, useToast } from "../ui.jsx";

export default function MyApplications() {
  const { t } = useT();
  const toast = useToast();
  const [apps, setApps] = useState(null);
  useEffect(() => {
    api.get("/my-applications/").then((r) => setApps(r.data.results || r.data))
      .catch((e) => { setApps([]); toast(errorText(e), "err"); });
  }, []);

  async function withdraw(a) {
    if (!window.confirm(`Withdraw your application for "${a.job_title}"?`)) return;
    try { await api.delete(`/my-applications/${a.id}/`); setApps(apps.filter((x) => x.id !== a.id)); toast("Application withdrawn"); }
    catch (e) { toast(errorText(e), "err"); }
  }
  async function view(a) { try { await openResume(a.resume); } catch (e) { toast(errorText(e, "Could not open the file."), "err"); } }

  return (
    <div className="stack">
      <h1>{t("myAppsTitle")}</h1>
      {apps === null ? <Skeleton /> : apps.length === 0 ? (
        <Empty icon="📝" title={t("noApps")}>{t("noAppsSub")} <Link to="/jobs" style={{ color: "var(--accent)" }}>{t("findJobs")}</Link></Empty>
      ) : apps.map((a) => (
        <div className={`card ${a.status === "selected" ? "success" : ""} ${a.status === "rejected" ? "rejected" : ""}`} key={a.id}>
          <div className="row between" style={{ flexWrap: "nowrap", alignItems: "flex-start" }}>
            <div>
              <h3>{a.job_title} <StatusBadge status={a.status} /></h3>
              <p className="muted">{a.company} · {a.job_location || "—"} · {ago(a.created_at, t)}</p>
            </div>
            <MatchRing value={a.match_percentage} size={72} />
          </div>
          {a.recruiter_note && (
            <div className="note"><b>💬 {t("fromRecruiter")}</b><p>{a.recruiter_note}</p></div>
          )}
          <div className="stack" style={{ marginTop: 14 }}>
            <Bar label={t("skills")} value={a.skill_score} />
            <Bar label={t("experience")} value={a.experience_score} />
            <Bar label={t("education")} value={a.education_score} />
          </div>
          <div style={{ marginTop: 12 }}>
            {a.matched_skills.map((s) => <span className="chip ok" key={s}>✓ {skillLabel(s)}</span>)}
            {a.missing_skills.map((s) => <span className="chip miss" key={s}>✗ {skillLabel(s)}</span>)}
          </div>
          <div className="row" style={{ marginTop: 14 }}>
            <Link className="btn" to={`/jobs/${a.job}`}>{t("viewDetails")}</Link>
            <button onClick={() => view(a)}>📄 {t("resume")}</button>
            {a.status !== "selected" && <button className="danger" onClick={() => withdraw(a)}>Withdraw</button>}
          </div>
        </div>
      ))}
    </div>
  );
}
