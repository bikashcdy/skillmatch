import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

export default function Register() {
  const [form, setForm] = useState({
    username: "", email: "", password: "", role: "candidate", company_name: "",
  });
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    try {
      await api.post("/auth/register/", form);
      navigate("/login");
    } catch (err) {
      setError(JSON.stringify(err.response?.data || "Registration failed"));
    }
  }

  return (
    <form className="card narrow" onSubmit={submit}>
      <h2>Create account</h2>
      {error && <p className="error">{error}</p>}
      <select value={form.role} onChange={set("role")}>
        <option value="candidate">I'm looking for a job</option>
        <option value="recruiter">I'm hiring (recruiter)</option>
      </select>
      <input placeholder="Username" value={form.username} onChange={set("username")} required />
      <input type="email" placeholder="Email" value={form.email} onChange={set("email")} required />
      <input type="password" placeholder="Password (min 8 chars)" value={form.password}
             onChange={set("password")} required />
      {form.role === "recruiter" && (
        <input placeholder="Company name" value={form.company_name}
               onChange={set("company_name")} required />
      )}
      <button className="primary">Register</button>
    </form>
  );
}
