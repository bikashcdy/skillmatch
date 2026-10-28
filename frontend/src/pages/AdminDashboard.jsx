import { useEffect, useState } from "react";
import api, { currentUser, errorText } from "../api";
import { Skeleton, useToast } from "../ui.jsx";

export default function AdminDashboard() {
  const toast = useToast();
  const me = currentUser();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState(null);
  const [filter, setFilter] = useState("");
  const [q, setQ] = useState("");

  const load = () => {
    api.get("/admin/stats/").then((r) => setStats(r.data));
    api.get("/admin/users/").then((r) => setUsers(r.data.results || r.data));
  };
  useEffect(() => { load(); }, []);

  async function toggle(u) {
    try { await api.post(`/admin/users/${u.id}/toggle/`); load(); }
    catch (e) { toast(errorText(e), "err"); }
  }
  const shown = (users || []).filter((u) => (!filter || u.role === filter) &&
    (u.username + u.email).toLowerCase().includes(q.toLowerCase()));
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
      <div className="card">
        <div className="row between" style={{ marginBottom: 12 }}>
          <h2>Users</h2>
          <div className="row">
            <input style={{ width: 200 }} placeholder="Search users…" value={q} onChange={(e) => setQ(e.target.value)} />
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
                  <td><b>{u.username}</b><br /><small>{u.email}</small></td>
                  <td style={{ textTransform: "capitalize" }}>{u.role}</td>
                  <td>{u.date_joined ? new Date(u.date_joined).toLocaleDateString() : "—"}</td>
                  <td><span className={`badge ${u.is_active ? "selected" : "rejected"}`}>{u.is_active ? "Active" : "Disabled"}</span></td>
                  <td>{u.id !== me.id && <button className={u.is_active ? "danger" : ""} onClick={() => toggle(u)}>{u.is_active ? "Deactivate" : "Activate"}</button>}</td>
                </tr>
              ))}
              {users && !shown.length && <tr><td colSpan="5" className="muted">No users found.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
