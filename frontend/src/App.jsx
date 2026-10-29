import { useEffect, useState } from "react";
import { Navigate, NavLink, Route, Routes, useNavigate } from "react-router-dom";
import { currentUser, logout } from "./api";
import { ToastProvider } from "./ui.jsx";
import { useT } from "./i18n.jsx";
import HowItWorks from "./pages/HowItWorks.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Jobs from "./pages/Jobs.jsx";
import MyApplications from "./pages/MyApplications.jsx";
import RecruiterDashboard from "./pages/RecruiterDashboard.jsx";
import Candidates from "./pages/Candidates.jsx";
import Recommendations from "./pages/Recommendations.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";

function Protected({ roles, children }) {
  const user = currentUser();
  if (!user) return <Navigate to="/login" replace />;
  if (!roles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
}

function Home() {
  const user = currentUser();
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={{ candidate: "/jobs", recruiter: "/recruiter", admin: "/admin" }[user.role]} replace />;
}

export default function App() {
  const user = currentUser();
  const navigate = useNavigate();
  const { t, lang, setLang } = useT();
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "");
  useEffect(() => {
    if (theme) document.documentElement.dataset.theme = theme;
    else delete document.documentElement.dataset.theme;
    try { localStorage.setItem("theme", theme); } catch {}
  }, [theme]);
  const dark = theme ? theme === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;

  return (
    <ToastProvider>
      <nav className="nav">
        <div className="nav-in">
          <NavLink to="/" className="brand"><i>J</i>JobMitra</NavLink>
          <div className="links">
            {user?.role === "candidate" && (<><NavLink to="/jobs">{t("findJobs")}</NavLink><NavLink to="/my-applications">{t("myApps")}</NavLink><NavLink to="/recommendations">{t("careerPlan")}</NavLink></>)}
            {user?.role === "recruiter" && <NavLink to="/recruiter">{t("myJobs")}</NavLink>}
            {user?.role === "admin" && <NavLink to="/admin">{t("admin")}</NavLink>}
          </div>
          <div className="nav-right">
            <button className="lang" title="Language / भाषा" onClick={() => setLang(lang === "en" ? "ne" : "en")}>{lang === "en" ? "नेपाली" : "EN"}</button>
            <button className="icon-btn" title="Toggle dark mode" onClick={() => setTheme(dark ? "light" : "dark")}>{dark ? "☀" : "☾"}</button>
            {user ? (
              <>
                <div className="avatar">{user.username[0].toUpperCase()}</div>
                <div className="who"><b>{user.username}</b><small>{user.role}</small></div>
                <button onClick={() => { logout(); navigate("/login"); window.location.reload(); }}>{t("logout")}</button>
              </>
            ) : (
              <>
                <NavLink className="btn" to="/login">{t("login")}</NavLink>
                <NavLink className="btn primary" to="/register">{t("signup")}</NavLink>
              </>
            )}
          </div>
        </div>
      </nav>
      <main className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/jobs" element={<Protected roles={["candidate"]}><Jobs /></Protected>} />
          <Route path="/my-applications" element={<Protected roles={["candidate"]}><MyApplications /></Protected>} />
          <Route path="/recommendations" element={<Protected roles={["candidate"]}><Recommendations /></Protected>} />
          <Route path="/recruiter" element={<Protected roles={["recruiter"]}><RecruiterDashboard /></Protected>} />
          <Route path="/recruiter/jobs/:id" element={<Protected roles={["recruiter"]}><Candidates /></Protected>} />
          <Route path="/admin" element={<Protected roles={["admin"]}><AdminDashboard /></Protected>} />
          <Route path="/how-it-works" element={<HowItWorks />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </main>
      <footer className="footer">
        <span>© JobMitra · BCA project</span>
        <NavLink to="/how-it-works">{t("howItWorks")}</NavLink>
      </footer>
    </ToastProvider>
  );
}
