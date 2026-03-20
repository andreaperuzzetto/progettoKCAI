const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Token storage ──────────────────────────────────────────────────

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setToken(token: string) {
  localStorage.setItem("access_token", token);
}

export function clearToken() {
  localStorage.removeItem("access_token");
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ── Auth API ────────────────────────────────────────────────────────

export interface RestaurantInfo {
  id: string;
  name: string;
}

export interface UserContext {
  user_id: string;
  email: string;
  restaurants: RestaurantInfo[];
}

export async function register(email: string, password: string): Promise<{ access_token: string }> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Registration failed");
  }
  return res.json();
}

export async function login(email: string, password: string): Promise<{ access_token: string }> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Login failed");
  }
  return res.json();
}

export async function fetchMe(): Promise<UserContext> {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Not authenticated");
  return res.json();
}

export async function createRestaurant(name: string): Promise<RestaurantInfo> {
  const res = await fetch(`${API_BASE}/auth/restaurants`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Failed to create restaurant");
  }
  return res.json();
}

// ── Operational API ─────────────────────────────────────────────────

export async function fetchDailyReport(restaurantId: string, targetDate: string) {
  const params = new URLSearchParams({ restaurant_id: restaurantId, target_date: targetDate });
  const res = await fetch(`${API_BASE}/daily-report?${params}`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch daily report");
  return res.json();
}

export async function fetchReviewAnalysis(restaurantId: string) {
  const params = new URLSearchParams({ restaurant_id: restaurantId });
  const res = await fetch(`${API_BASE}/review-analysis?${params}`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch review analysis");
  return res.json();
}

export async function fetchCorrelation(restaurantId: string) {
  const params = new URLSearchParams({ restaurant_id: restaurantId });
  const res = await fetch(`${API_BASE}/correlation?${params}`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch correlation");
  return res.json();
}

export async function uploadSales(restaurantId: string, file: File) {
  const params = new URLSearchParams({ restaurant_id: restaurantId });
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/upload-sales?${params}`, {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  if (!res.ok) throw new Error("Failed to upload sales");
  return res.json();
}

export async function uploadReviews(restaurantId: string, file: File) {
  const params = new URLSearchParams({ restaurant_id: restaurantId });
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/upload-reviews?${params}`, {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  if (!res.ok) throw new Error("Failed to upload reviews");
  return res.json();
}

