# Technical Assumptions — Restaurant Intelligence Platform

These are the architectural and implementation assumptions that underpin the system design. They should be revisited as the system grows.

---

## Infrastructure

### T1. PostgreSQL as the only datastore
**Assumption:** A single PostgreSQL instance is sufficient for MVP scale.  
**Implication:** No Redis, no message queue, no distributed cache.  
**Risk:** Under high load (thousands of restaurants), scheduled jobs may contend with API traffic on the same DB.  
**Mitigation plan:** Add read replicas or move scheduled jobs to a separate worker process.

---

### T2. APScheduler in-process is sufficient for background jobs
**Assumption:** Scheduled jobs (forecast generation, email dispatch, alert detection) can run in the same process as the FastAPI application without impacting API latency.  
**Implication:** No separate Celery/Redis worker infrastructure.  
**Risk:** Long-running jobs (e.g., forecasting for 1000+ restaurants) block the scheduler thread pool.  
**Mitigation plan:** Move to Celery + Redis if job runtime exceeds 30 seconds on a typical server.

---

### T3. SQLite compatibility is maintained
**Assumption:** The ORM models should remain compatible with SQLite for local development and testing.  
**Implication:** UUID columns use `CHAR(32)` (not PostgreSQL-native UUID). `JSON` columns are used instead of PostgreSQL-specific `JSONB`.  
**Risk:** Loss of PostgreSQL-specific optimizations (indexes on JSON, full-text search).

---

## Security

### T4. JWT stored in localStorage is acceptable for MVP
**Assumption:** Storing JWT tokens in `localStorage` is acceptable for the MVP phase despite the XSS risk.  
**Implication:** No `httpOnly` cookie implementation.  
**Risk:** XSS vulnerability could expose tokens.  
**Mitigation plan:** Migrate to `httpOnly` cookie-based auth before public launch.

---

### T5. CORS restricted to localhost:3000 is a dev-only config
**Assumption:** The current CORS configuration (`allow_origins=["http://localhost:3000"]`) must be updated before production deployment.  
**Implication:** Backend and frontend domains must be configured in `main.py` for production.

---

## Data Model

### T6. One restaurant per owner is the common case
**Assumption:** Most users will have one restaurant. The multi-restaurant and organization features are built for completeness but not the primary use case.  
**Implication:** UI defaults to the first restaurant in the user's list.

---

### T7. Sales records are append-only
**Assumption:** CSV uploads add new records without deduplication.  
**Implication:** Re-uploading the same CSV will create duplicate records.  
**Risk:** Inflated sales data will distort forecasts and analysis.  
**Mitigation plan:** Add upsert logic based on `(restaurant_id, date, product_name)` uniqueness.

---

### T8. AnalysisResult replaces, not appends
**Assumption:** Each `run_analysis` call stores a new result but the system always reads the latest one.  
**Implication:** Historical analysis results are preserved but the dashboard shows only the most recent.

---

## AI / ML

### T9. LinearRegression is sufficient for 7-day forecasting
**Assumption:** A linear model with day-of-week + rolling average features is accurate enough for planning purposes in the MVP.  
**Implication:** No time-series models (ARIMA, Prophet, LSTM).  
**Risk:** Non-linear demand patterns (holidays, seasonal peaks) will be under-predicted.  
**Mitigation plan:** Add a `holiday` feature flag and seasonal correction in v2.

---

### T10. One model per product is computationally feasible
**Assumption:** Training a separate LinearRegression model for each product at forecast time is fast enough (< 1 second per product).  
**Implication:** No batch pre-training or model persistence; models are retrained on every forecast call.  
**Risk:** Restaurants with 50+ distinct products may see latency spikes.

---

### T11. OpenAI API failures are non-critical
**Assumption:** All LLM-dependent features (correlations, insights) have a working rule-based fallback, so API downtime or missing API key never blocks the user.  
**Implication:** LLM errors are logged as warnings, not errors. The system silently falls back.

---

## Frontend

### T12. No state management library needed
**Assumption:** React Context is sufficient for the MVP's auth and restaurant state management.  
**Implication:** No Redux, Zustand, or Jotai.  
**Risk:** As the app grows in complexity, prop drilling and context re-renders may become a problem.

---

### T13. All API calls are made client-side
**Assumption:** There is no server-side rendering (SSR) for data-fetching; all `fetch()` calls happen in the browser after hydration.  
**Implication:** No `getServerSideProps` or Server Components making API calls.  
**Risk:** Initial page load shows a loading state until data is fetched.

---

## Scaling Thresholds

When the following thresholds are approached, the corresponding architectural assumptions should be revisited:

| Threshold | Assumption at risk | Suggested action |
|-----------|-------------------|-----------------|
| > 500 restaurants | T2 (in-process scheduler) | Move to Celery workers |
| > 100 products per restaurant | T10 (per-product model training) | Pre-train and cache models |
| > 10k API req/min | T1 (single PostgreSQL) | Add read replicas |
| > 50k reviews per restaurant | T9 (LinearRegression) | Evaluate time-series models |
