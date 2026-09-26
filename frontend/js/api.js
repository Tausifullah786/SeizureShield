/* Shared API helper — attaches the JWT and handles errors. */

const TOKEN_KEY = "ss_token";
const DOCTOR_KEY = "ss_doctor";

const auth = {
  save(token, doctor) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(DOCTOR_KEY, JSON.stringify(doctor));
  },
  token() { return localStorage.getItem(TOKEN_KEY); },
  doctor() {
    const raw = localStorage.getItem(DOCTOR_KEY);
    return raw ? JSON.parse(raw) : null;
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(DOCTOR_KEY);
  },
};

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };

  const token = auth.token();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  // Don't set Content-Type for FormData — the browser adds the boundary itself
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`/api${path}`, { ...options, headers });

  if (res.status === 401) {
    auth.clear();
    window.location.href = "login.html";
    throw new Error("Session expired");
  }

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") message = data.detail;
      else if (Array.isArray(data.detail)) message = data.detail[0].msg;
    } catch { /* keep the default message */ }
    throw new Error(message);
  }

  return res.status === 204 ? null : res.json();
}

const api = {
  signup: (body) => request("/auth/signup", { method: "POST", body: JSON.stringify(body) }),
  login: (body) => request("/auth/login", { method: "POST", body: JSON.stringify(body) }),
  google: (credential) => request("/auth/google", { method: "POST", body: JSON.stringify({ credential }) }),
  me: () => request("/auth/me"),

  listPatients: () => request("/patients"),
  getPatient: (id) => request(`/patients/${id}`),
  createPatient: (body) => request("/patients", { method: "POST", body: JSON.stringify(body) }),
  deletePatient: (id) => request(`/patients/${id}`, { method: "DELETE" }),

  uploadAnalysis: (patientId, file) => {
    const fd = new FormData();
    fd.append("file", file);
    return request(`/patients/${patientId}/analyses`, { method: "POST", body: fd });
  },
  listAnalyses: (patientId) =>
    request(`/analyses${patientId ? `?patient_id=${patientId}` : ""}`),
  getAnalysis: (id) => request(`/analyses/${id}`),

  modelInfo: () => request("/model/info"),
};