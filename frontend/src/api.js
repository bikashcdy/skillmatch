import axios from "axios";

// Works on localhost and on 127.0.0.1 (same host as the page, port 8000).
const BASE = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000/api`;
const api = axios.create({ baseURL: BASE });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// When the short-lived access token expires, silently get a new one with the refresh token.
let refreshing = null;
api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config;
    const refresh = localStorage.getItem("refresh");
    if (error.response?.status === 401 && refresh && original && !original._retry
        && !original.url.includes("/auth/")) {
      original._retry = true;
      try {
        refreshing = refreshing || axios.post(`${BASE}/auth/refresh/`, { refresh });
        const { data } = await refreshing;
        refreshing = null;
        localStorage.setItem("access", data.access);
        if (data.refresh) localStorage.setItem("refresh", data.refresh);
        original.headers.Authorization = `Bearer ${data.access}`;
        return api(original);
      } catch (e) {
        refreshing = null;
        logout();
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export async function login(username, password) {
  const { data } = await api.post("/auth/login/", { username, password });
  localStorage.setItem("access", data.access);
  localStorage.setItem("refresh", data.refresh);
  const me = await api.get("/auth/me/");
  localStorage.setItem("user", JSON.stringify(me.data));
  return me.data;
}

export function logout() {
  ["access", "refresh", "user"].forEach((k) => localStorage.removeItem(k));
}

export const currentUser = () => {
  try { return JSON.parse(localStorage.getItem("user") || "null"); } catch { return null; }
};

// Resume files are private: fetch with the login token. PDFs, images and text open in a new tab;
// Word files (which browsers cannot display) are downloaded instead.
export async function openResume(resumeId) {
  const res = await api.get(`/resumes/${resumeId}/file/`, { responseType: "blob" });
  const type = res.data.type || "";
  const disposition = res.headers["content-disposition"] || "";
  const name = decodeURIComponent((disposition.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i) || [])[1] || "resume");
  const url = URL.createObjectURL(res.data);
  if (type === "application/pdf" || type.startsWith("image/") || type.startsWith("text/")) {
    window.open(url, "_blank");
  } else {
    const link = document.createElement("a");
    link.href = url;
    link.download = name;
    document.body.appendChild(link);
    link.click();
    link.remove();
  }
  setTimeout(() => URL.revokeObjectURL(url), 60000);
}

// Keep the saved user (role, approval) up to date, e.g. after an admin approves a recruiter.
export async function refreshUser() {
  const { data } = await api.get("/auth/me/");
  localStorage.setItem("user", JSON.stringify(data));
  return data;
}

// Turn any API error into a short human sentence.
export function errorText(err, fallback = "Something went wrong.") {
  if (!err.response) return "Cannot reach the server. Is the backend running on port 8000?";
  const d = err.response.data;
  if (typeof d === "string") return fallback;
  if (d?.detail) return d.detail;
  if (d && typeof d === "object") {
    return Object.entries(d)
      .map(([k, v]) => `${k === "non_field_errors" ? "" : k.replace(/_/g, " ") + ": "}${[].concat(v).join(" ")}`)
      .join("  ");
  }
  return fallback;
}

export default api;
