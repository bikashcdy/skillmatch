import { Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { currentUser, logout } from "./api";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Jobs from "./pages/Jobs.jsx";
import MyApplications from "./pages/MyApplications.jsx";
import RecruiterDashboard from "./pages/RecruiterDashboard.jsx";
import Candidates from "./pages/Candidates.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";

function Protected({ roles, children }) {
  const user = currentUser();
  if (!user) return <Navigate to="/login" />;
  if (!roles.includes(user.role)) return <Navigate to="/" />;
  return children;
}

function Home() {
  const user = currentUser();
  if (!user) return <Navigate to="/login" />;
  const dest = { candidate: "/jobs", recruiter: "/recruiter", admin: "/admin" }[user.role];
  return <Navigate to={dest} />;
}

export default function App() {
  const user = currentUser();
  const navigate = useNavigate();
  return (
    <>
      <nav className="nav">
        <Link to="/" className="brand">SkillMatch AI</Link>
        <div className="links">
          {user?.role === "candidate" && (<><Link to="/jobs">Jobs</Link><Link to="/my-applications">My applications</Link></>)}
          {user?.role === "recruiter" && <Link to="/recruiter">My jobs</Link>}
          {user?.role === "admin" && <Link to="/admin">Admin</Link>}
          {user ? (
            <button onClick={() => { logout(); navigate("/login"); window.location.reload(); }}>
              Log out ({user.username})
            </button>
          ) : (<><Link to="/login">Log in</Link><Link to="/register">Register</Link></>)}
        </div>
      </nav>
      <main className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/jobs" element={<Protected roles={["candidate"]}><Jobs /></Protected>} />
          <Route path="/my-applications" element={<Protected roles={["candidate"]}><MyApplications /></Protected>} />
          <Route path="/recruiter" element={<Protected roles={["recruiter"]}><RecruiterDashboard /></Protected>} />
          <Route path="/recruiter/jobs/:id" element={<Protected roles={["recruiter"]}><Candidates /></Protected>} />
          <Route path="/admin" element={<Protected roles={["admin"]}><AdminDashboard /></Protected>} />
        </Routes>
      </main>
    </>
  );
}
