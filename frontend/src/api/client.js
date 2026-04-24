// Thin fetch wrapper with Bearer-token auth + 401 auto-redirect.
// Kept small on purpose: this is a teaching app, not a production SDK.

const BASE = import.meta.env.VITE_API_BASE || "";
const TOKEN_KEY = "aegis_token";

export const tokenStorage = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

// Subscribable 401 hook so the AuthContext can react to forced logouts.
let unauthorizedHandler = null;
export const onUnauthorized = (fn) => {
  unauthorizedHandler = fn;
};

async function request(path, { method = "GET", body, signal, form } = {}) {
  const headers = {};
  const token = tokenStorage.get();
  if (token) headers.Authorization = `Bearer ${token}`;

  let payload = undefined;
  if (form) {
    payload = new URLSearchParams(form).toString();
    headers["Content-Type"] = "application/x-www-form-urlencoded";
  } else if (body !== undefined) {
    payload = JSON.stringify(body);
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${BASE}${path}`, { method, headers, body: payload, signal });

  if (res.status === 401) {
    tokenStorage.clear();
    if (unauthorizedHandler) unauthorizedHandler();
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    let detail = text;
    try {
      const j = JSON.parse(text);
      detail = j.detail || text;
    } catch {
      /* not JSON */
    }
    throw new Error(`${res.status} ${res.statusText} - ${detail}`);
  }

  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

export const api = {
  health: () => request("/api/health"),

  // Auth
  authConfig: () => request("/api/auth/config"),
  login: (username, password) =>
    request("/api/auth/login", { method: "POST", form: { username, password } }),
  register: (payload) => request("/api/auth/register", { method: "POST", body: payload }),
  me: () => request("/api/auth/me"),
  changePassword: (current_password, new_password) =>
    request("/api/auth/change-password", {
      method: "POST",
      body: { current_password, new_password },
    }),

  // Settings
  getSettings: () => request("/api/settings/"),
  getSettingsSchema: () => request("/api/settings/schema"),
  updateLLMSettings: (body) => request("/api/settings/llm", { method: "PUT", body }),
  updateAgenticSettings: (body) => request("/api/settings/agentic", { method: "PUT", body }),
  updateGuardrailSettings: (body) => request("/api/settings/guardrails", { method: "PUT", body }),
  updateLabSettings: (body) => request("/api/settings/lab", { method: "PUT", body }),
  resetSettings: () => request("/api/settings/reset", { method: "POST" }),

  // Users (admin)
  listUsers: () => request("/api/users/"),
  createUser: (body) => request("/api/users/", { method: "POST", body }),
  updateRole: (id, role) =>
    request(`/api/users/${id}/role`, { method: "PATCH", body: { role } }),
  resetPassword: (id, new_password) =>
    request(`/api/users/${id}/reset-password`, { method: "POST", body: { new_password } }),
  deleteUser: (id) => request(`/api/users/${id}`, { method: "DELETE" }),

  // Attack Lab
  runAttack: (payload) => request("/api/attack/run", { method: "POST", body: payload }),
  getPresets: () => request("/api/attack/presets"),
  getRagDoc: () => request("/api/attack/rag-document"),
  getModels: () => request("/api/attack/models"),
  getAttackTypes: () => request("/api/attack/attack-types"),

  // Education Hub
  listVulnerabilities: () => request("/api/education/vulnerabilities"),
  getVulnerability: (id) => request(`/api/education/vulnerabilities/${id}`),
  listCategories: () => request("/api/education/categories"),
  getPrimer: () => request("/api/education/primer"),
  getPrimerChapter: (chapterId) => request(`/api/education/primer/${chapterId}`),

  // Agentic Sandbox
  runAgent: (payload) => request("/api/agentic/run", { method: "POST", body: payload }),

  // Stress Lab
  runStress: (payload) => request("/api/stress/run", { method: "POST", body: payload }),

  // Dashboard
  getMetrics: () => request("/api/metrics/"),
  clearMetrics: () => request("/api/metrics/", { method: "DELETE" }),
};
