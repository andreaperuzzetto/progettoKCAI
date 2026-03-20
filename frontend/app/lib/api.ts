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

// ── Auth ────────────────────────────────────────────────────────────

export interface RestaurantInfo {
  id: string;
  name: string;
}

export interface UserContext {
  user_id: string;
  email: string;
  subscription_status: "active" | "inactive" | "trial";
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
  const res = await fetch(`${API_BASE}/auth/me`, { headers: authHeaders() });
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

// ── Reviews ─────────────────────────────────────────────────────────

export async function uploadReviewsCsv(restaurantId: string, file: File) {
  const params = new URLSearchParams({ restaurant_id: restaurantId });
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/reviews/upload?${params}`, {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Failed to upload reviews");
  }
  return res.json();
}

export async function uploadReviewsText(restaurantId: string, reviews: string[]) {
  const params = new URLSearchParams({ restaurant_id: restaurantId });
  const res = await fetch(`${API_BASE}/reviews/upload-text?${params}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ reviews }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Failed to upload reviews");
  }
  return res.json();
}

// ── Analysis ─────────────────────────────────────────────────────────

export interface Issue {
  name: string;
  frequency: number;
}

export interface Suggestion {
  problem: string;
  action: string;
}

export interface AnalysisData {
  id: string;
  period: string;
  sentiment: {
    positive_percentage: number;
    negative_percentage: number;
  };
  issues: Issue[];
  strengths: Issue[];
  suggestions: Suggestion[];
  created_at: string;
}

export async function runAnalysis(restaurantId: string, period = "all"): Promise<AnalysisData> {
  const params = new URLSearchParams({ restaurant_id: restaurantId, period });
  const res = await fetch(`${API_BASE}/analysis/run?${params}`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Analysis failed");
  }
  const data = await res.json();
  return data as AnalysisData;
}

export async function fetchLatestAnalysis(restaurantId: string): Promise<AnalysisData | null> {
  const params = new URLSearchParams({ restaurant_id: restaurantId });
  const res = await fetch(`${API_BASE}/analysis/latest?${params}`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch analysis");
  const data = await res.json();
  return data.analysis ?? null;
}

// ── Billing ──────────────────────────────────────────────────────────

export async function createCheckoutSession(): Promise<{ checkout_url: string }> {
  const res = await fetch(`${API_BASE}/billing/checkout`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Billing error");
  }
  return res.json();
}
