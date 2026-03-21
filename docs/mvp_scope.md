# MVP Scope — Restaurant Intelligence Platform

## What the MVP Delivers

The MVP covers 5 core capabilities that form a complete decision cycle for restaurant operators:

---

### 1. Sales Data Upload & Summary
**What:** Upload historical sales records via CSV.  
**Format:** `date, product, quantity` (optional: `revenue`)  
**Output:** Top products, daily totals, period summary.  
**Why:** Sales data is the foundation for forecasting and operational planning.

---

### 2. Customer Reviews Import & Sentiment Analysis
**What:** Upload reviews via CSV or paste text directly.  
**Format:** `date, platform, review_text, rating`  
**Output:**
- Positive / negative sentiment percentage
- Top complaint topics with frequency counts
- Recurring strengths
- Suggested corrective actions

**Why:** Reviews contain the "why" behind sales trends. Connecting them to operations is the platform's core differentiation.

---

### 3. Demand Forecasting (7-Day Horizon)
**What:** AI-generated daily demand predictions for the next 7 days.  
**Output:** Expected covers + per-product quantity predictions.  
**Algorithm:** LinearRegression on day-of-week patterns + rolling averages. Weighted moving average fallback for sparse data.  
**Why:** Every operational decision (staffing, purchasing) depends on knowing how busy tomorrow will be.

---

### 4. Daily Operational Report
**What:** A single aggregated report combining all data sources.  
**Output:**
- Tomorrow's expected covers and top products
- 7-day forecast overview
- Prioritized operational suggestions (inventory, staffing, menu)
- Review sentiment summary and top issues
- Active alerts

**Delivery:** Available in the dashboard and sent by email every morning at 07:00.  
**Why:** This is the single daily touchpoint. If an owner reads only one thing, it should be this.

---

### 5. Alerts & Correlations
**What:** Proactive detection of 5 alert conditions + causal analysis.

**Alert types:**
- High demand spike (tomorrow ≥ +30% vs average)
- Negative review spike (+15 percentage points)
- Sales drop (-30% over last 3 days)
- Low overall sentiment (< 40% positive)
- Recurring issue increase (frequency delta ≥ 2)

**Correlations:** Rule-based (and optionally LLM-based) mapping of review issues to operational suggestions, taking tomorrow's forecast into account.

**Why:** Owners can't monitor data constantly. The system monitors for them and surfaces only what requires action.

---

## What Is In Scope

| Feature | Included |
|---------|---------|
| User registration + JWT authentication | ✅ |
| Restaurant creation (per user) | ✅ |
| Sales CSV import | ✅ |
| Reviews CSV + text import | ✅ |
| Sentiment analysis (keyword-based) | ✅ |
| 7-day demand forecast | ✅ |
| Daily report (dashboard + email) | ✅ |
| Alerts (5 types) | ✅ |
| Rule-based correlations | ✅ |
| LLM correlations (GPT-4o-mini, optional) | ✅ |
| Menu optimization (2×2 matrix) | ✅ |
| Purchase order generation | ✅ |
| Staff planning | ✅ |
| AI insights (top 3 daily) | ✅ |
| Subscription plans (Starter / Pro / Premium) | ✅ |
| Stripe billing integration | ✅ |
| Multi-restaurant per user | ✅ |
| Organizations (multi-user, chains) | ✅ |
| Third-party integrations (Google Sheets, etc.) | ✅ |

---

## What Is NOT in the MVP Scope

| Feature | Reason |
|---------|--------|
| Mobile app | Web-first MVP; mobile in Phase 6 |
| Real-time POS sync | Complex integration; manual CSV is sufficient for validation |
| Advanced ML models (LSTM, Prophet) | LinearRegression is sufficient and explainable |
| Customer-facing review response tool | Out of scope; focus is operational decisions |
| Inventory stock tracking | Requires hardware integration; out of scope |
| Supplier management | Separate product category |
| Multi-language UI (non-Italian) | Italian-first for initial market |

---

## Feature Flags by Plan

| Feature | Trial | Starter | Pro | Premium |
|---------|-------|---------|-----|---------|
| Basic analysis | ✅ | ✅ | ✅ | ✅ |
| Forecasting | ✅ | ✅ | ✅ | ✅ |
| Daily report | ✅ | ✅ | ✅ | ✅ |
| Alerts | ✅ | ❌ | ✅ | ✅ |
| LLM correlations | ✅ | ❌ | ✅ | ✅ |
| Menu optimization | ✅ | ❌ | ✅ | ✅ |
| Operations | ✅ | ❌ | ✅ | ✅ |
| AI Insights | ✅ | ❌ | ✅ | ✅ |
| Integrations | ✅ | ❌ | ❌ | ✅ |
| Organizations | ✅ | ❌ | ❌ | ✅ |

*Trial: all features for 7 days. After trial expires, account moves to `inactive` until subscription is activated.*
