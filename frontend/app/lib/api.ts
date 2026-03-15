const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchDailyReport(
  restaurantId: string,
  targetDate: string
) {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
    target_date: targetDate,
  });
  const res = await fetch(`${API_BASE}/daily-report?${params}`);
  if (!res.ok) throw new Error("Failed to fetch daily report");
  return res.json();
}

export async function fetchReviewAnalysis(restaurantId: string) {
  const params = new URLSearchParams({ restaurant_id: restaurantId });
  const res = await fetch(`${API_BASE}/review-analysis?${params}`);
  if (!res.ok) throw new Error("Failed to fetch review analysis");
  return res.json();
}

export async function fetchCorrelation(restaurantId: string) {
  const params = new URLSearchParams({ restaurant_id: restaurantId });
  const res = await fetch(`${API_BASE}/correlation?${params}`);
  if (!res.ok) throw new Error("Failed to fetch correlation");
  return res.json();
}

export async function uploadSales(restaurantId: string, file: File) {
  const params = new URLSearchParams({ restaurant_id: restaurantId });
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/upload-sales?${params}`, {
    method: "POST",
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
    body: form,
  });
  if (!res.ok) throw new Error("Failed to upload reviews");
  return res.json();
}
