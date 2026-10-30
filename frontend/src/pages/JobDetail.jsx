import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api, { errorText } from "../api";
import ApplyModal from "../ApplyModal.jsx";
import { useT } from "../i18n.jsx";
import { Empty, MatchRing, Skeleton, StatusBadge, ago, eduText, expText, expiryText, formatDate, salaryText, skillLabel, useToast } from "../ui.jsx";

export default function JobDetail() {
  const { id } = useParams();
  const { t } = useT();
  const toast = useToast();
  const [job, setJob] = useState(undefined); // undefined = loading, null = not found
  const [apply, setApply] = useState(false);

  const load = () => api.get(`/jobs/${id}/`).then((r) => setJob(r.data))
    .catch((e) => { setJob(null); if (e.response?.status !== 404) toast(errorText(e), "err"); });
  useEffect(() => { setJob(undefined); load(); window.scrollTo(0, 0); }, [id]);

  if (job === undefined) return <Skeleton n={3} />;
  if (job === null) {
    return (
      <div className="stack">
        <Link to="/jobs" className="muted">← {t("backToJobs")}</Link>
        <Empty icon="⏳" title={t("jobGone")}>{t("jobGoneSub")}</Empty>
      </div>
    );
  }
  const md = job.match_detail;
  const urgent = job.days_left != null && job.days_left <= 3;
  const facts = [
    ["📍", t("location"), job.location || "—"],
    ["💼", t("jobType"), t(job.job_type)],
    ["💰", "Salary", salaryText(job, t)],
    ["⏱", t("experienceReq"), job.min_experience_years > 0 ? t("expYears", { n: job.min_experience_years }) : t("fresher")],
    ["🎓", t("qualification"), eduText(job.required_education, t)],
    ["🕒", t("posted"), `${ago(job.created_at, t)} · ${formatDate(job.created_at.slice(0, 10))}`],
    ["⏳", t("expires"), job.expires_at ? `${formatDate(job.expires_at)} · ${expiryText(job, t)}` : t("noDeadline")],
  ];

  return (
    <div className="stack">
      <Link to="/jobs" className="muted">← {t("backToJobs")}</Link>
      <div className="detail">
        <div className="stack">
          <section className="card">
            <div className="row" style={{ flexWrap: "nowrap", alignItems: "flex-start" }}>
              <div className="logo big">{job.company[0]?.toUpperCase()}</div>
              <div>
                <h1>{job.title}</h1>
                <p className="muted">{job.company}</p>
                <div style={{ marginTop: 8 }}>
                  <span className={`badge type-${job.job_type}`}>{t(job.job_type)}</span>{" "}
                  {urgent && <span className="badge rejected">⏳ {expiryText(job, t)}</span>}
                </div>
              </div>
            </div>
          </section>

          <section className="card">
            <h2 style={{ marginBottom: 12 }}>{t("jobDetails")}</h2>
            <div className="facts">
              {facts.map(([i, k, v]) => (
                <div className="fact" key={k}><span className="fi">{i}</span><div><small>{k}</small><b>{v}</b></div></div>
              ))}
            </div>
          </section>

          <section className="card">
            <h2 style={{ marginBottom: 8 }}>{t("description")}</h2>
            <p className="prose">{job.description}</p>
          </section>

          <section className="card">
            <h2 style={{ marginBottom: 8 }}>{t("requirements")}</h2>
            <ul className="reqs">
              <li><b>{t("requiredSkills")}:</b> {job.required_skills.map((s) => <span className="chip" key={s}>{skillLabel(s)}</span>)}</li>
              <li><b>{t("experienceReq")}:</b> {job.min_experience_years > 0 ? t("expYears", { n: job.min_experience_years }) : t("fresher")}</li>
              <li><b>{t("qualification")}:</b> {eduText(job.required_education, t)}</li>
            </ul>
          </section>
        </div>

        <aside className="stack side-card">
          <section className="card center">
            {job.my_application ? (
              <><StatusBadge status={job.my_application.status} /><p className="muted" style={{ marginTop: 8 }}>{t("alreadyApplied")}</p></>
            ) : (
              <button className="primary wide" onClick={() => setApply(true)}>{t("applyNow")}</button>
            )}
          </section>
          <section className="card center">
            <h3 style={{ marginBottom: 10 }}>{t("yourResume")}</h3>
            {md ? (
              <>
                <div style={{ display: "grid", placeItems: "center" }}><MatchRing value={md.match_percentage} size={92} /></div>
                <div style={{ marginTop: 12, textAlign: "left" }}>
                  <small>{t("matchedSkills")}</small><br />
                  {md.matched_skills.length ? md.matched_skills.map((s) => <span className="chip ok" key={s}>✓ {skillLabel(s)}</span>) : <span className="muted">—</span>}
                  <br /><small>{t("missingSkills")}</small><br />
                  {md.missing_skills.length ? md.missing_skills.map((s) => <span className="chip miss" key={s}>✗ {skillLabel(s)}</span>) : <span className="muted">—</span>}
                </div>
              </>
            ) : <p className="muted">{t("uploadForMatch")}</p>}
          </section>
        </aside>
      </div>
      {apply && <ApplyModal job={job} onClose={() => setApply(false)} onDone={() => { setApply(false); load(); }} />}
    </div>
  );
}
