import { useEffect, useState } from "react";
import api from "../api";

export default function AdminDashboard() {
  const [stats, setStats] = useState({});
  const [users, setUsers] = useState([]);

  const load = () => {
    api.get("/admin/stats/").then((r) => setStats(r.data));
    api.get("/admin/users/").then((r) => setUsers(r.data));
  };
  useEffect(() => { load(); }, []);

  async function toggle(id) {
    await api.post(`/admin/users/${id}/toggle/`);
    load();
  }

  return (
    <>
      <h1>Admin</h1>
      <div className="stats">
        {Object.entries(stats).map(([k, v]) => (
          <div className="card stat" key={k}><strong>{v}</strong><span>{k}</span></div>
        ))}
      </div>
      <h2>Users</h2>
      <table className="table">
        <thead><tr><th>Username</th><th>Email</th><th>Role</th><th>Active</th><th /></tr></thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.username}</td><td>{u.email}</td><td>{u.role}</td>
              <td>{u.is_active ? "yes" : "no"}</td>
              <td><button onClick={() => toggle(u.id)}>{u.is_active ? "Deactivate" : "Activate"}</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
