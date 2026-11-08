import { useEffect, useState } from "react";
import api, { currentUser, errorText, openResume, refreshUser } from "../api";
import { Checklist, FieldError, PasswordInput } from "../ui_extra.jsx";
import { Modal, Skeleton, skillLabel, ago, useToast } from "../ui.jsx";
import { ResumeReview } from "../ui_resume.jsx";
import { useT } from "../i18n.jsx";
import { companyErrors, emailErrors, jobLocationErrors, passwordOk, passwordRules } from "../validate.js";

export default function Profile() {
  const { t } = useT();
  const toast = useToast();
  const me = currentUser();
  const [form, setForm] = useState({ email: me.email || "", company_name: me.company_name || "" });
  const [errs, setErrs] = useState({});
  const [pw, setPw] = useState({ old_password: "", new_password: "", confirm: "" });
  const [resumes, setResumes] = useState(null);
  const [prefs, setPrefs] = useState({ preferred_location: me.preferred_location || "", preferred_job_type: me.preferred_job_type || "" });
  const [prefErr, setPrefErr] = useState([]);
  const [review, setReview] = useState(null);

  const loadResumes = () => me.role === "candidate" && api.get("/resumes/").then((r) => setResumes(r.data)).catch(() => setResumes([]));
  useEffect(() => { refreshUser().then((u) => { setForm({ email: u.email, company_name: u.company_name }); setPrefs({ preferred_location: u.preferred_location || "", preferred_job_type: u.preferred_job_type || "" }); }); loadResumes(); }, []);

  async function savePrefs(e) {
    e.preventDefault();
    const bad = prefs.preferred_location.trim() ? jobLocationErrors(prefs.preferred_location) : [];
    setPrefErr(bad);
    if (bad.length) return;
    try { await api.patch("/auth/me/", prefs); await refreshUser(); toast("Job preferences saved"); }
    catch (ex) { toast(errorText(ex), "err"); }
  }

  async function saveProfile(e) {
    e.preventDefault();
    const e1 = emailErrors(form.email), e2 = me.role === "recruiter" ? companyErrors(form.company_name) : [];
    setErrs({ email: e1, company_name: e2 });
    if (e1.length || e2.length) return;
    try { await api.patch("/auth/me/", form); await refreshUser(); toast("Profile saved"); }
    catch (ex) {
      const d = ex.response?.data;
      if (d && typeof d === "object" && !d.detail) setErrs(Object.fromEntries(Object.entries(d).map(([k, v]) => [k, [].concat(v)])));
      else toast(errorText(ex), "err");
    }
  }
  async function changePassword(e) {
    e.preventDefault();
    try {
      await api.post("/auth/change-password/", { old_password: pw.old_password, new_password: pw.new_password });
      setPw({ old_password: "", new_password: "", confirm: "" }); toast("Password changed");
    } catch (ex) { toast(errorText(ex), "err"); }
  }
  async function remove(r) {
    if (!window.confirm(`Delete resume "${r.filename}"? The file will be removed from our server.`)) return;
    try { await api.delete(`/resumes/${r.id}/`); toast("Resume deleted"); loadResumes(); }
    catch (ex) { toast(errorText(ex), "err"); }
  }
  async function view(r) { try { await openResume(r.id); } catch (ex) { toast(errorText(ex, "Could not open the file."), "err"); } }

  const pwValid = passwordOk(pw.new_password, me.username, form.email) && pw.new_password === pw.confirm && pw.old_password;

  return (
    <div className="stack" style={{ maxWidth: 760, margin: "0 auto" }}>
      <h1>{t("profile")}</h1>
      <form className="card stack" onSubmit={saveProfile} noValidate>
        <h2>Account</h2>
        <div><label className="f">{t("username")}</label><input value={me.username} disabled /></div>
        <div><label className="f">{t("email")}</label>
          <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className={errs.email?.length ? "bad" : ""} />
          <FieldError errors={errs.email} /></div>
        {me.role === "recruiter" && (
          <div><label className="f">{t("company")}</label>
            <input value={form.company_name} onChange={(e) => setForm({ ...form, company_name: e.target.value })} className={errs.company_name?.length ? "bad" : ""} />
            <FieldError errors={errs.company_name} /></div>
        )}
        <div><button className="primary">{t("saveChanges")}</button></div>
      </form>

      <form className="card stack" onSubmit={changePassword}>
        <h2>Change password</h2>
        <PasswordInput placeholder="Current password" autoComplete="current-password" value={pw.old_password} onChange={(e) => setPw({ ...pw, old_password: e.target.value })} />
        <div><PasswordInput placeholder="New password" value={pw.new_password} onChange={(e) => setPw({ ...pw, new_password: e.target.value })} />
          {pw.new_password && <Checklist rules={passwordRules(pw.new_password, me.username, form.email)} />}</div>
        <div><PasswordInput placeholder="Confirm new password" value={pw.confirm} onChange={(e) => setPw({ ...pw, confirm: e.target.value })} />
          <FieldError errors={pw.confirm && pw.confirm !== pw.new_password ? ["Passwords do not match."] : []} /></div>
        <div><button className="primary" disabled={!pwValid}>Change password</button></div>
      </form>

      {me.role === "candidate" && (
        <form className="card stack" onSubmit={savePrefs} noValidate>
          <h2>Job preferences</h2>
          <p className="muted">Optional. When you set them, jobs in your city or of your job type score a little higher. Leave empty to skip.</p>
          <div className="grid2">
            <div><label className="f">Preferred city</label>
              <input value={prefs.preferred_location} maxLength={60} placeholder="e.g. Pokhara" className={prefErr.length ? "bad" : ""}
                onChange={(e) => setPrefs({ ...prefs, preferred_location: e.target.value })} />
              <FieldError errors={prefErr} /></div>
            <div><label className="f">Preferred job type</label>
              <select value={prefs.preferred_job_type} onChange={(e) => setPrefs({ ...prefs, preferred_job_type: e.target.value })}>
                <option value="">No preference</option>
                {["full_time", "part_time", "internship", "contract"].map((x) => <option key={x} value={x}>{t(x)}</option>)}
              </select></div>
          </div>
          <div><button className="primary">Save preferences</button></div>
        </form>
      )}

      {me.role === "candidate" && (
        <section className="card stack">
          <div className="row between"><h2>My resumes</h2>
            <button type="button" onClick={() => setReview({ resume: null, manual: true })}>＋ Type my details</button></div>
          <p className="muted">Only you, and recruiters of jobs you applied to, can open these files.</p>
          {resumes === null ? <Skeleton n={1} /> : resumes.length === 0 ? <p className="muted">No resume uploaded yet. Upload one from the Career plan page or when you apply.</p> :
            resumes.map((r) => (
              <div className="row between resume-row" key={r.id}>
                <div>
                  <b>📄 {r.filename || "Typed details"}</b> {!r.confirmed && <span className="badge auto">Needs your confirmation</span>}
                  <p className="muted" style={{ fontSize: 13.5 }}>Uploaded {ago(r.uploaded_at, t)} · {r.experience_years} yr · used in {r.applications} application(s)</p>
                  <div>{r.extracted_skills.slice(0, 8).map((s) => <span className="chip" key={s}>{skillLabel(s)}</span>)}</div>
                </div>
                <div className="row">
                  {!r.confirmed && <button className="primary" onClick={() => setReview({ resume: r, manual: false })}>Review</button>}
                  {r.filename && <button onClick={() => view(r)}>Open</button>}
                  <button className="danger" onClick={() => remove(r)}>{t("del")}</button>
                </div>
              </div>
            ))}
        </section>
      )}
      {review && (
        <Modal title="Check your resume details" onClose={() => setReview(null)}>
          <ResumeReview resume={review.resume} manual={review.manual} onCancel={() => setReview(null)}
            onDone={() => { setReview(null); loadResumes(); }} />
        </Modal>
      )}
    </div>
  );
}
