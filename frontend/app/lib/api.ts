const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Token storage ─────────────────────────────────────────────────────────────
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}
export function setToken(token: string) { localStorage.setItem("token", token); }
export function clearToken() { localStorage.removeItem("token"); }
export function authHeaders(): Record<string, string> {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

// ── Types ─────────────────────────────────────────────────────────────────────
export interface RestaurantInfo { id: string; name: string }
export interface UserContext {
  user_id: string;
  email: string;
  subscription_status: string;
  plan: string;
  restaurants: RestaurantInfo[];
}
export interface Issue { name: string; frequency: number }
export interface AnalysisSuggestion { problem: string; action: string }
export interface AnalysisData {
  id: string;
  period: string;
  sentiment: { positive_percentage: number; negative_percentage: number };
  issues: Issue[];
  strengths: Issue[];
  suggestions: AnalysisSuggestion[];
}
export interface SalesSummary {
  period_days: number;
  total_records: number;
  top_products: { name: string; total_quantity: number }[];
  daily_totals: { date: string; total_quantity: number }[];
}
export interface ForecastDay {
  id: string;
  date: string;
  expected_covers: number;
  product_predictions: Record<string, number>;
}
export interface Suggestion {
  type: string;
  message: string;
  priority: "high" | "medium" | "low";
  source?: string;
}
export interface Correlation {
  cause: string;
  confidence: number;
  suggestion: string;
  impact_level: "high" | "medium" | "low";
}
export interface AlertItem {
  id: string;
  type: string;
  severity: "high" | "medium" | "low";
  message: string;
  created_at: string;
  read: boolean;
}
export interface DailyReport {
  date: string;
  restaurant_id: string;
  tomorrow: { date: string; expected_covers: number; top_products: { name: string; predicted_qty: number }[] };
  forecast_7days: ForecastDay[];
  suggestions: Suggestion[];
  review_summary: { sentiment_positive: number | null; sentiment_negative: number | null; top_issues: Issue[] };
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export async function register(email: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "Registrazione fallita"); }
  return res.json();
}
export async function login(email: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "Accesso fallito"); }
  return res.json();
}
export async function fetchMe(): Promise<UserContext> {
  const res = await fetch(`${API_BASE}/auth/me`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Non autenticato");
  return res.json();
}
export async function createRestaurant(name: string): Promise<RestaurantInfo> {
  const res = await fetch(`${API_BASE}/auth/restaurants`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "Errore"); }
  return res.json();
}

// ── Reviews ───────────────────────────────────────────────────────────────────
export async function uploadReviewsCsv(restaurantId: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/reviews/upload?restaurant_id=${restaurantId}`, {
    method: "POST", headers: authHeaders(), body: form,
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "Upload fallito"); }
  return res.json();
}
export async function uploadReviewsText(restaurantId: string, reviews: string[]) {
  const res = await fetch(`${API_BASE}/reviews/upload-text?restaurant_id=${restaurantId}`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ reviews }),
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "Upload fallito"); }
  return res.json();
}

// ── Analysis ──────────────────────────────────────────────────────────────────
export async function runAnalysis(restaurantId: string, period = "all"): Promise<AnalysisData> {
  const res = await fetch(`${API_BASE}/analysis/run?restaurant_id=${restaurantId}&period=${period}`, {
    method: "POST", headers: authHeaders(),
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "Analisi fallita"); }
  return res.json();
}
export async function fetchLatestAnalysis(restaurantId: string): Promise<AnalysisData | null> {
  const res = await fetch(`${API_BASE}/analysis/latest?restaurant_id=${restaurantId}`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Impossibile caricare analisi");
  const data = await res.json();
  return data.analysis ?? null;
}

// ── Sales ─────────────────────────────────────────────────────────────────────
export async function uploadSalesCsv(restaurantId: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/sales/upload?restaurant_id=${restaurantId}`, {
    method: "POST", headers: authHeaders(), body: form,
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "Upload vendite fallito"); }
  return res.json();
}

// ── Forecast ──────────────────────────────────────────────────────────────────
export async function generateForecast(restaurantId: string) {
  const res = await fetch(`${API_BASE}/forecast/generate?restaurant_id=${restaurantId}`, {
    method: "POST", headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Generazione previsione fallita");
  return res.json();
}

// ── Daily Report ──────────────────────────────────────────────────────────────
export async function fetchDailyReport(restaurantId: string): Promise<DailyReport> {
  const res = await fetch(`${API_BASE}/daily-report?restaurant_id=${restaurantId}`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Impossibile caricare report giornaliero");
  return res.json();
}

// ── Alerts ────────────────────────────────────────────────────────────────────
export async function generateAlerts(restaurantId: string) {
  const res = await fetch(`${API_BASE}/alerts/generate?restaurant_id=${restaurantId}`, {
    method: "POST", headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Errore nella generazione alert");
  return res.json();
}
export async function fetchAlerts(restaurantId: string, unreadOnly = false): Promise<{ alerts: AlertItem[]; unread_count: number }> {
  const res = await fetch(`${API_BASE}/alerts?restaurant_id=${restaurantId}&unread_only=${unreadOnly}`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Impossibile caricare alert");
  return res.json();
}
export async function markAlertRead(restaurantId: string, alertId: string) {
  await fetch(`${API_BASE}/alerts/${alertId}/read?restaurant_id=${restaurantId}`, {
    method: "POST", headers: authHeaders(),
  });
}

// ── Correlations ──────────────────────────────────────────────────────────────
export async function fetchLatestCorrelation(restaurantId: string): Promise<{ correlations: Correlation[] }> {
  const res = await fetch(`${API_BASE}/correlations/latest?restaurant_id=${restaurantId}`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Impossibile caricare correlazioni");
  return res.json();
}
export async function runCorrelation(restaurantId: string): Promise<{ correlations: Correlation[] }> {
  const res = await fetch(`${API_BASE}/correlations/run?restaurant_id=${restaurantId}`, {
    method: "POST", headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Correlazione fallita");
  return res.json();
}

// ── Billing ───────────────────────────────────────────────────────────────────
export async function createCheckoutSession(plan: "starter" | "pro" | "premium" = "starter"): Promise<{ checkout_url: string }> {
  const res = await fetch(`${API_BASE}/billing/checkout`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ plan }),
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "Errore checkout"); }
  return res.json();
}

// ── Integrations ──────────────────────────────────────────────────────────────
export async function listIntegrations(restaurantId: string) {
  const res = await fetch(`${API_BASE}/integrations?restaurant_id=${restaurantId}`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Impossibile caricare integrazioni");
  return res.json();
}
export async function createIntegration(restaurantId: string, provider: string, config: Record<string, string>) {
  const res = await fetch(`${API_BASE}/integrations?restaurant_id=${restaurantId}`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ provider, config }),
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "Errore"); }
  return res.json();
}
export async function syncIntegration(restaurantId: string, integrationId: string) {
  const res = await fetch(`${API_BASE}/integrations/${integrationId}/sync?restaurant_id=${restaurantId}`, {
    method: "POST", headers: authHeaders(),
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "Sync fallito"); }
  return res.json();
}

// ── Menu Optimization ─────────────────────────────────────────────────────────
export interface ProductMetric {
  product: string;
  total_quantity: number;
  total_revenue: number;
  avg_daily_quantity: number;
  popularity_score: number;
  revenue_score: number;
}
export interface MenuSuggestion {
  product: string;
  action: "promote" | "optimize_price" | "reposition" | "remove" | "monitor";
  reason: string;
  priority: "high" | "medium" | "low";
}
export async function analyzeMenu(restaurantId: string): Promise<{ suggestions: MenuSuggestion[] }> {
  const res = await fetch(`${API_BASE}/menu/analyze?restaurant_id=${restaurantId}`, {
    method: "POST", headers: authHeaders(),
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "Analisi menu fallita"); }
  return res.json();
}
export async function fetchMenuMetrics(restaurantId: string): Promise<{ metrics: ProductMetric[] }> {
  const res = await fetch(`${API_BASE}/menu/metrics?restaurant_id=${restaurantId}`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Impossibile caricare metriche menu");
  return res.json();
}

// ── Operations ────────────────────────────────────────────────────────────────
export interface PurchaseOrderItem {
  ingredient: string;
  quantity: number;
  unit: string;
  suggested_supplier?: string;
}
export interface StaffShift {
  date: string;
  day_of_week: string;
  expected_covers: number;
  recommended_staff: number;
  shift_notes: string;
}
export async function generatePurchaseOrder(restaurantId: string): Promise<{ items: PurchaseOrderItem[]; generated_at: string }> {
  const res = await fetch(`${API_BASE}/operations/purchase-order?restaurant_id=${restaurantId}`, {
    method: "POST", headers: authHeaders(),
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "Errore ordine acquisti"); }
  return res.json();
}
export async function fetchStaffPlan(restaurantId: string): Promise<{ shifts: StaffShift[] }> {
  const res = await fetch(`${API_BASE}/operations/staff-plan?restaurant_id=${restaurantId}`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Impossibile caricare piano staff");
  return res.json();
}

// ── Insights ──────────────────────────────────────────────────────────────────
export interface InsightItem {
  id: string;
  type: string;
  message: string;
  confidence: number;
  impact: number;
  read_at?: string;
  created_at: string;
}
export async function generateInsights(restaurantId: string): Promise<{ insights: InsightItem[] }> {
  const res = await fetch(`${API_BASE}/insights/generate?restaurant_id=${restaurantId}`, {
    method: "POST", headers: authHeaders(),
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "Errore generazione insights"); }
  return res.json();
}
export async function fetchLatestInsights(restaurantId: string): Promise<{ insights: InsightItem[] }> {
  const res = await fetch(`${API_BASE}/insights/latest?restaurant_id=${restaurantId}`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Impossibile caricare insights");
  return res.json();
}
export async function markInsightRead(restaurantId: string, insightId: string) {
  const res = await fetch(`${API_BASE}/insights/${insightId}/read?restaurant_id=${restaurantId}`, {
    method: "POST", headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Errore");
  return res.json();
}

// ── Organizations ─────────────────────────────────────────────────────────────
export interface OrgRestaurant { id: string; name: string; city?: string; category?: string }
export interface OrgContext { id: string; name: string; role: string; restaurants: OrgRestaurant[] }
export async function fetchMyOrg(): Promise<OrgContext | null> {
  const res = await fetch(`${API_BASE}/organizations/me`, { headers: authHeaders() });
  if (!res.ok) return null;
  return res.json();
}
export async function createOrganization(name: string): Promise<OrgContext> {
  const res = await fetch(`${API_BASE}/organizations`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "Errore"); }
  return res.json();
}
export async function compareLocations(orgId: string): Promise<{ comparison: unknown }> {
  const res = await fetch(`${API_BASE}/organizations/compare?org_id=${orgId}`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Impossibile confrontare sedi");
  return res.json();
}

// ── Restaurant metadata ───────────────────────────────────────────────────────
export async function updateRestaurant(restaurantId: string, data: { city?: string; category?: string }) {
  const res = await fetch(`${API_BASE}/restaurants/${restaurantId}`, {
    method: "PATCH",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "Errore aggiornamento"); }
  return res.json();
}
