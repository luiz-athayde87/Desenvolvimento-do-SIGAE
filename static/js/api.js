export const session = {
  authenticated: false,
  authRequired: false,
  user: null,
  csrfToken: null,
};

export async function request(path, options = {}) {
  const method = String(options.method || "GET").toUpperCase();
  const headers = { ...(options.headers || {}) };
  if (options.body && !headers["Content-Type"]) headers["Content-Type"] = "application/json";
  if (!["GET", "HEAD", "OPTIONS"].includes(method) && session.csrfToken) {
    headers["X-CSRF-Token"] = session.csrfToken;
  }
  const response = await fetch(path, { ...options, method, headers, credentials: "same-origin" });
  const contentType = response.headers.get("content-type") || "";
  const payload = response.status === 204
    ? null
    : contentType.includes("application/json")
      ? await response.json()
      : await response.text();
  if (!response.ok) {
    const error = new Error(payload?.error?.message || `A operação falhou (${response.status}).`);
    error.status = response.status;
    error.code = payload?.error?.code;
    error.fields = payload?.error?.fields || {};
    if (response.status === 401) window.dispatchEvent(new CustomEvent("sigae:auth-required"));
    throw error;
  }
  return payload?.data ?? payload;
}

export async function loadSession() {
  const data = await request("/api/v1/auth/me");
  session.authenticated = Boolean(data.authenticated);
  session.authRequired = Boolean(data.auth_required);
  session.user = data.user || null;
  session.csrfToken = data.csrf_token || null;
  return session;
}

export async function login(username, password) {
  const data = await request("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  session.authenticated = true;
  session.user = data.user;
  session.csrfToken = data.csrf_token;
  return session;
}

export async function logout() {
  await request("/api/v1/auth/logout", { method: "POST" });
  session.authenticated = false;
  session.user = null;
  session.csrfToken = null;
}
