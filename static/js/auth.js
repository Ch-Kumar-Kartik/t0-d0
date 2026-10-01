import { getErrorMessage } from "./utils.js";

let currentUser = null;
let currentUserRequest = null;

function getToken() {
  return localStorage.getItem("access_token");
}

function setToken(token) {
  localStorage.setItem("access_token", token);
}

function clearToken() {
  localStorage.removeItem("access_token");
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const error = new Error(getErrorMessage(body));
    error.status = response.status;
    error.body = body;
    throw error;
  }

  return body;
}

export async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = getToken();

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return parseResponse(await fetch(path, { ...options, headers }));
}

export async function register({ username, email, password }) {
  return apiRequest("/api/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });
}

export async function login(email, password) {
  const form = new URLSearchParams({ username: email, password });
  const response = await fetch("/api/users/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form,
  });
  const data = await parseResponse(response);
  setToken(data.access_token);
  currentUser = null;
  return data;
}

export async function getCurrentUser() {
  if (currentUser) {
    return currentUser;
  }

  if (!getToken()) {
    return null;
  }

  if (currentUserRequest) {
    return currentUserRequest;
  }

  currentUserRequest = apiRequest("/api/users/me")
    .then((user) => {
      currentUser = user;
      return user;
    })
    .catch((error) => {
      if (error.status === 401) {
        clearToken();
      }
      return null;
    })
    .finally(() => {
      currentUserRequest = null;
    });

  return currentUserRequest;
}

export async function logout() {
  try {
    await apiRequest("/api/users/logout", { method: "POST" });
  } catch {
    // Clearing this browser's token is sufficient for a stateless JWT logout.
  }
  clearToken();
  currentUser = null;
  window.location.assign("/login");
}

export function clearUserCache() {
  currentUser = null;
}

export { clearToken, getToken, setToken };
