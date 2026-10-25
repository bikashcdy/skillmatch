import axios from "axios";

const api = axios.create({ baseURL: "http://localhost:8000/api" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function login(username, password) {
  const { data } = await api.post("/auth/login/", { username, password });
  localStorage.setItem("access", data.access);
  const me = await api.get("/auth/me/");
  localStorage.setItem("user", JSON.stringify(me.data));
  return me.data;
}

export function logout() {
  localStorage.removeItem("access");
  localStorage.removeItem("user");
}

export const currentUser = () => JSON.parse(localStorage.getItem("user") || "null");

export default api;
