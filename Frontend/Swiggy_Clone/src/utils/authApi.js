import { AUTH_BASE_URL } from "../config";

// Thin wrapper around AuthService (Express + Prisma). Stores the JWT and
// user info in localStorage so the rest of the app can read "is anyone
// logged in" the same way it already reads Cart/user_details.

async function request(path, body) {
  const res = await fetch(`${AUTH_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || "Something went wrong. Please try again.");
  }
  return data; // { token, user }
}

export function signup({ email, password, name }) {
  return request("/auth/signup", { email, password, name });
}

export function login({ email, password }) {
  return request("/auth/login", { email, password });
}

// Passwordless login: request() throws on a non-2xx response, so a rejected
// promise here already means "couldn't send the code" — the caller doesn't
// need to separately check success.
export function requestOtp({ email }) {
  return request("/auth/otp/request", { email });
}

export function verifyOtp({ email, code }) {
  return request("/auth/otp/verify", { email, code });
}

export function storeAuth({ token, user }) {
  localStorage.setItem("authToken", token);
  localStorage.setItem("authUser", JSON.stringify(user));
}

export function getStoredAuth() {
  const token = localStorage.getItem("authToken");
  const user = JSON.parse(localStorage.getItem("authUser") || "null");
  return token && user ? { token, user } : null;
}

export function clearAuth() {
  localStorage.removeItem("authToken");
  localStorage.removeItem("authUser");
}

// fetch() wrapper for calling authenticated backend endpoints (e.g. FastAPI's
// /orders). Attaches the token automatically, and — since a JWT here expires
// after JWT_EXPIRES_IN (1h) — reacts to a 401 by clearing the stale token and
// reloading, so the navbar and the rest of the page fall back to "signed
// out" together instead of getting stuck showing a raw error while the nav
// still displays the old (now-invalid) logged-in name.
export async function authFetch(url, options = {}) {
  const auth = getStoredAuth();
  if (!auth) {
    throw new Error("Not signed in");
  }

  const res = await fetch(url, {
    ...options,
    headers: { ...(options.headers || {}), Authorization: `Bearer ${auth.token}` },
  });

  if (res.status === 401) {
    clearAuth();
    alert("Your session has expired. Please sign in again.");
    window.location.reload();
    throw new Error("Session expired"); // stop the caller's .then chain; reload is already in flight
  }

  return res;
}
