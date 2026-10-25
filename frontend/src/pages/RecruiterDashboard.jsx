import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api";

const empty = { title: "", description: "", location: "", skills: "", min_experience_years: 0, required_education: "" };

export default function RecruiterDashboard() {
  const [jobs, setJobs] = useState([]);
  const [form, setForm] = useState(empty);
  const [error, setError] = useState("");
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const load = () => api.get("/recruiter/jobs/").then((r) => setJobs(r.data.results || r.data));
  useEffect(() => { load(); }, []);

  async function create(e) {
    e.preventDefault();
    try {
      await api.post("/recruiter/jobs/", {
        ...form,
        required_skills: form.skills.split(",").map((s) => s.trim()).filter(Boolean),
      });
      setForm(empty);
      setError("");
      load();
    } catch (err) {
      setError(JSON.stringify(err.response?.data || "Failed to post job"));
    }
  }

  return (
    <>
      <h1>Post a job</h1>
      <form className="card" onSubmit={create}>
        {error && <p className="error">{error}</p>}
        <input placeholder="Job title" value={form.title} onChange={set("title")} required />
        <textarea placeholder="Description" value={form.description} onChange={set("description")} required />
        <input placeholder="Location" value={form.location} onChange={set("location")} />
        <input placeholder="Required skills, comma separated (python, django, react)"
               value={form.skills} onChange={set("skills")} required />
        <div className="row">
          <input type="number" min="0" step="0.5" placeholder="Min experience (years)"
                 value={form.min_experience_years} onChange={set("min_experience_years")} />
          <select value={form.required_education} onChange={set("required_education")}>
            <option value="">Any education</option>
            <option value="diploma">Diploma / +2</option>
            <option value="bachelor">Bachelor</option>
            <option value="master">Master</option>
            <option value="phd">PhD</option>
          </select>
        </div>
        <button className="primary">Publish job</button>
      </form>

      <h2>Your jobs</h2>
      {jobs.map((j) => (
        <div className="card row between" key={j.id}>
          <div>
            <h3>{j.title}</h3>
            <p className="muted">{j.applicants} applicant(s)</p>
          </div>
          <Link className="btn" to={`/recruiter/jobs/${j.id}`}>View ranked candidates</Link>
        </div>
      ))}
    </>
  );
}
