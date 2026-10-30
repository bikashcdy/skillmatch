import { useEffect, useState } from "react";
import api, { currentUser, errorText } from "../api";
import { Skeleton, formatDate, useToast } from "../ui.jsx";

export default function AdminDashboard() {
  const toast = useToast();
  const me = currentUser();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState(null);
  const [jobs, setJobs] = useState(null);
  const [tab, setTab] = useState("users");
  const [filter, setFilter] = useState("");
  const [q, setQ] = useState("");

  const load = () => {
    api.get("/admin/stats/").then((r) => setStats(r.data));
    api.get("/admin/users/").then((r) => setUsers(r.data.results || r.data));
    api.get("/admin/jobs/").then((r) => setJobs(r.data));
  };
  useEffect(() => { load(); }, []);

  const run = async (fn, ok) => { try { await fn(); if (ok) toast(ok); load(); } catch (e) { toast(errorText(e), "err"); } };
  const toggle = (u) => run(() => api.post(`/admin/users/${u.id}/toggle/`));
  const approve = (u, approved) => run(() => api.post(`/admin/users/${u.id}/approve/`, { approved }), approved ? "Recruiter approved" : "Recruiter un-approved (their jobs are hidden)");
  const removeJob = (j) => window.confirm(`Delete job "${j.title}" (${j.company}) and its ${j.applicants} application(s)? This cannot be undone.`) &&
    run(() => api.delete(`/admin/jobs/${j.id}/`), "Job deleted");

  const pending = (users || []).filter((u) => u.role === "recruiter" && !u.is_approved);
  const shown = (users || []).filter((u) => (!filter || u.role === filter) && (u.username + u.email + u.company_name).toLowerCase().includes(q.toLowerCase()));
  const cards = stats && [["👥", stats.users, "Candidates"], ["🧑‍💼", stats.recruiters, "Recruiters"], ["💼", stats.jobs, "Jobs"],
    ["📝", stats.applications, "Applications"], ["✅", stats.selected, "Selected"]];

  return (
    <div className="stack">
      <h1>Admin dashboard</h1>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(170px,1fr))", gap: 14 }}>
        {!cards ? <Skeleton n={1} /> : cards.map(([i, n, l]) => (
          <div className="card stat" key={l}><div className="ico">{i}</div><div><b>{n}</b><span>{l}</span></div></div>
        ))}
      </div>

      {pending.length > 0 && (
        <section className="card pending">
          <h2>⏳ Recruiters waiting for approval ({pending.length})</h2>
          {pending.map((u) => (
            <div className="row between resume-row" key={u.id}>
              <div><b>{u.company_name}</b><p className="muted">{u.username} · {u.email} · registered {formatDate(u.date_joined.slice(0, 10))}</p></div>
              <div className="row"><button className="primary" onClick={() => approve(u, true)}>Approve</button>
                <button className="danger" onClick={() => toggle(u)}>Reject &amp; deactivate</button></div>
            </div>
          ))}
        </section>
      )}

      <div className="seg" style={{ maxWidth: 320 }}>
        <button className={tab === "users" ? "on" : ""} onClick={() => setTab("users")}>Users</button>
        <button className={tab === "jobs" ? "on" : ""} onClick={() => setTab("jobs")}>Jobs ({jobs ? jobs.length : "…"})</button>
      </div>

      {tab === "users" ? (
        <div className="card">
          <div className="row between" style={{ marginBottom: 12 }}>
            <h2>Users</h2>
            <div className="row">
              <input style={{ width: 220 }} placeholder="Search name, email, company…" value={q} onChange={(e) => setQ(e.target.value)} />
              <select style={{ width: 150 }} value={filter} onChange={(e) => setFilter(e.target.value)}>
                <option value="">All roles</option><option value="candidate">Candidates</option>
                <option value="recruiter">Recruiters</option><option value="admin">Admins</option>
              </select>
            </div>
          </div>
          <div className="tablewrap">
            <table>
              <thead><tr><th>User</th><th>Role</th><th>Joined</th><th>Status</th><th></th></tr></thead>
              <tbody>
                {shown.map((u) => (
                  <tr key={u.id}>
                    <td><b>{u.username}</b><br /><small>{u.email}{u.company_name ? ` · ${u.company_name}` : ""}</small></td>
                    <td style={{ textTransform: "capitalize" }}>{u.role}</td>
                    <td>{u.date_joined ? new Date(u.date_joined).toLocaleDateString() : "—"}</td>
                    <td>
                      <span className={`badge ${u.is_active ? "selected" : "rejected"}`}>{u.is_active ? "Active" : "Disabled"}</span>{" "}
                      {u.role === "recruiter" && <span className={`badge ${u.is_approved ? "selected" : "auto"}`}>{u.is_approved ? "Approved" : "Pending"}</span>}
                    </td>
                    <td className="row" style={{ flexWrap: "nowrap" }}>
                      {u.role === "recruiter" && (u.is_approved
                        ? <button onClick={() => approve(u, false)}>Un-approve</button>
                        : <button className="primary" onClick={() => approve(u, true)}>Approve</button>)}
                      {u.id !== me.id && <button className={u.is_active ? "danger" : ""} onClick={() => toggle(u)}>{u.is_active ? "Deactivate" : "Activate"}</button>}
                    </td>
                  </tr>
                ))}
                {users && !shown.length && <tr><td colSpan="5" className="muted">No users found.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="card">
          <h2 style={{ marginBottom: 12 }}>All jobs</h2>
          <div className="tablewrap">
            <table>
              <thead><tr><th>Job</th><th>Recruiter</th><th>Location</th><th>Applicants</th><th>Status</th><th></th></tr></thead>
              <tbody>
                {(jobs || []).map((j) => (
                  <tr key={j.id}>
                    <td><b>{j.title}</b><br /><small>{j.company} · posted {formatDate(j.created_at.slice(0, 10))}</small></td>
                    <td>{j.recruiter}</td><td>{j.location || "—"}</td><td>{j.applicants}</td>
                    <td><span className={`badge ${j.is_expired || !j.is_open ? "rejected" : "selected"}`}>{!j.is_open ? "Closed" : j.is_expired ? "Expired" : "Live"}</span></td>
                    <td><button className="danger" onClick={() => removeJob(j)}>Delete</button></td>
                  </tr>
                ))}
                {jobs && !jobs.length && <tr><td colSpan="6" className="muted">No jobs.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
