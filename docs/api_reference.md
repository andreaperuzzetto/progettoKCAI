# API Reference — Restaurant Intelligence Platform

Base URL: `http://localhost:8000`

All authenticated endpoints require:
```
Authorization: Bearer <jwt_token>
```

Most endpoints require the `restaurant_id` query parameter (UUID).

---

## Authentication

### `POST /auth/register`
Register a new user. Automatically starts a 7-day trial.

**Body:**
```json
{ "email": "user@example.com", "password": "secret" }
```

**Response `201`:**
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

---

### `POST /auth/login`
Rate limited: 5 requests/minute per IP.

**Body:**
```json
{ "email": "user@example.com", "password": "secret" }
```

**Response `200`:**
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

---

### `GET /auth/me`
Returns the authenticated user's profile and restaurants.

**Response:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "subscription_status": "trial|active|inactive",
  "plan": "starter|pro|premium",
  "restaurants": [{ "id": "uuid", "name": "My Restaurant" }]
}
```

---

### `POST /auth/restaurants`
Create a new restaurant for the authenticated user.

**Body:** `{ "name": "My Restaurant" }`

**Response `201`:** `{ "id": "uuid", "name": "My Restaurant" }`

---

## Health

### `GET /health`
No authentication required.

**Response:** `{ "status": "ok" }`

---

## Reviews

### `POST /reviews/upload?restaurant_id=<uuid>`
Upload reviews from a CSV file.

**CSV columns:** `date, platform, review_text, rating`

**Body:** `multipart/form-data` with `file` field.

**Response:** `{ "imported": <count> }`

---

### `POST /reviews/upload-text?restaurant_id=<uuid>`
Upload reviews as plain text array.

**Body:** `{ "reviews": ["Great pizza", "Slow service"] }`

**Response:** `{ "imported": <count> }`

---

## Analysis

### `POST /analysis/run?restaurant_id=<uuid>&period=all`
Run sentiment analysis and topic extraction on all reviews.

**Query params:**
- `period`: `all` | `last_30_days`

**Response:**
```json
{
  "status": "ok",
  "id": "uuid",
  "period": "all",
  "sentiment": { "positive_percentage": 72.5, "negative_percentage": 27.5 },
  "issues": [{ "name": "slow service", "frequency": 8 }],
  "strengths": [{ "name": "great pizza", "frequency": 15 }],
  "suggestions": [{ "problem": "slow service", "action": "Add staff during peak hours" }]
}
```

---

### `GET /analysis/latest?restaurant_id=<uuid>`
Get the most recent analysis result.

**Response:** `{ "status": "ok", "analysis": <AnalysisData> | null }`

---

## Sales

### `POST /sales/upload?restaurant_id=<uuid>`
Upload sales data from a CSV file.

**CSV columns:** `date, product, quantity` (optional: `revenue`)

**Body:** `multipart/form-data` with `file` field.

**Response:** `{ "imported": <count> }`

---

### `GET /sales/summary?restaurant_id=<uuid>&days=30`
Get sales summary with top products and daily totals.

**Response:**
```json
{
  "period_days": 30,
  "total_records": 450,
  "top_products": [{ "name": "pizza", "total_quantity": 340 }],
  "daily_totals": [{ "date": "2025-01-01", "total_quantity": 87 }]
}
```

---

## Products

### `GET /products?restaurant_id=<uuid>`
List all products for a restaurant.

### `POST /products?restaurant_id=<uuid>`
Create a product. **Body:** `{ "name": "Pizza", "category": "main" }`

### `POST /products/{product_id}/ingredients?restaurant_id=<uuid>`
Add ingredient mapping to a product.

**Body:**
```json
{ "ingredient_name": "Farina", "quantity_per_unit": 0.3, "unit": "kg" }
```

---

## Forecast

### `POST /forecast/generate?restaurant_id=<uuid>`
Generate a 7-day demand forecast using LinearRegression on historical sales.

**Response:**
```json
{
  "forecast": [
    {
      "date": "2025-01-15",
      "expected_covers": 85,
      "product_predictions": { "pizza": 42, "pasta": 28 }
    }
  ]
}
```

---

### `GET /forecast/latest?restaurant_id=<uuid>`
Get the latest stored forecast.

---

## Daily Report

### `GET /daily-report?restaurant_id=<uuid>`
Aggregated operational report combining forecast, alerts, analysis, and suggestions.

**Response:**
```json
{
  "date": "2025-01-14",
  "restaurant_id": "uuid",
  "tomorrow": {
    "date": "2025-01-15",
    "expected_covers": 85,
    "top_products": [{ "name": "pizza", "predicted_qty": 42 }]
  },
  "forecast_7days": [...],
  "suggestions": [
    {
      "type": "staffing",
      "message": "Domani attesi 85 coperti (+30% vs media)...",
      "priority": "high",
      "source": "correlation"
    }
  ],
  "review_summary": {
    "sentiment_positive": 72.5,
    "sentiment_negative": 27.5,
    "top_issues": [{ "name": "slow service", "frequency": 8 }]
  }
}
```

---

## Alerts

### `POST /alerts/generate?restaurant_id=<uuid>`
Manually trigger alert detection (requires `alerts` feature on plan).

**Response:** `{ "generated": 2, "alerts": [...] }`

---

### `GET /alerts?restaurant_id=<uuid>&unread_only=false`
List alerts for the restaurant.

**Response:**
```json
{
  "alerts": [
    {
      "id": "uuid",
      "type": "high_demand|negative_spike|sales_drop|low_sentiment|issue_increase",
      "severity": "high|medium|low",
      "message": "Domani domanda alta: attesi 120 coperti (+45%)...",
      "created_at": "2025-01-14T08:00:00",
      "read": false
    }
  ],
  "unread_count": 1
}
```

---

### `POST /alerts/{alert_id}/read?restaurant_id=<uuid>`
Mark an alert as read.

---

## Correlations

### `POST /correlations/run?restaurant_id=<uuid>`
Run LLM-based (or rule-based fallback) causal correlation analysis.

**Response:**
```json
{
  "correlations": [
    {
      "cause": "personale insufficiente ore di punta",
      "confidence": 0.85,
      "suggestion": "Aggiungi 1-2 camerieri nelle fasce 19-22.",
      "impact_level": "high"
    }
  ]
}
```

---

### `GET /correlations/latest?restaurant_id=<uuid>`
Get the most recent stored correlation result.

---

## Insights

### `POST /insights/generate?restaurant_id=<uuid>`
Generate top-3 proactive insights (predictive, diagnostic, prescriptive).

### `GET /insights?restaurant_id=<uuid>`
List stored insights.

### `POST /insights/{insight_id}/read?restaurant_id=<uuid>`
Mark an insight as read.

---

## Menu

### `POST /menu/analyze?restaurant_id=<uuid>`
Run menu optimization analysis (2×2 matrix: popularity × revenue).

**Response:**
```json
{
  "suggestions": [
    {
      "product": "Pizza Margherita",
      "action": "promote|optimize_price|reposition|remove|monitor",
      "reason": "Alta popolarità e alto fatturato. Considera promozioni.",
      "priority": "high",
      "popularity_score": 0.92,
      "revenue_score": 0.88,
      "trend_7d": 5.2
    }
  ]
}
```

---

### `GET /menu/metrics?restaurant_id=<uuid>`
Get computed product metrics.

---

## Operations

### `POST /operations/purchase-order?restaurant_id=<uuid>`
Generate a purchase order based on 7-day forecast and product-ingredient mappings.

**Response:**
```json
{
  "items": [
    { "ingredient": "Farina", "quantity": 15.5, "unit": "kg" }
  ],
  "generated_at": "2025-01-14T10:00:00"
}
```

---

### `GET /operations/staff-plan?restaurant_id=<uuid>`
Get a 7-day staff planning recommendation based on forecast.

**Response:**
```json
{
  "shifts": [
    {
      "date": "2025-01-15",
      "day_of_week": "Wednesday",
      "expected_covers": 85,
      "recommended_staff": 4,
      "shift_notes": "Alta affluenza prevista"
    }
  ]
}
```

---

## Billing

### `POST /billing/checkout`
Create a Stripe checkout session.

**Body:** `{ "plan": "starter|pro|premium" }`

**Response:** `{ "checkout_url": "https://checkout.stripe.com/..." }`

---

### `POST /billing/webhook`
Stripe webhook endpoint (internal, not exposed in schema).

---

## Integrations

### `GET /integrations?restaurant_id=<uuid>`
List all integrations.

### `POST /integrations?restaurant_id=<uuid>`
Create a new integration.

**Body:** `{ "provider": "google_sheets", "config": { "sheet_id": "..." } }`

### `POST /integrations/{id}/sync?restaurant_id=<uuid>`
Manually trigger sync for an integration.

---

## Organizations

### `POST /organizations`
Create a new organization (multi-restaurant group).

### `GET /organizations/{org_id}/restaurants`
List all restaurants in an organization.

### `POST /organizations/{org_id}/members`
Invite a user to an organization.

---

## Error Codes

| Status | Meaning |
|--------|---------|
| `400` | Bad request / validation error |
| `401` | Missing or invalid JWT token |
| `402` | Subscription required |
| `403` | Resource not owned by user |
| `404` | Resource not found |
| `409` | Conflict (e.g., email already registered) |
| `422` | Pydantic validation error |
| `429` | Rate limit exceeded |
| `503` | External service not configured |
