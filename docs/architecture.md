# Architecture — Restaurant Intelligence Platform

## Overview

The platform follows a **3-tier layered architecture** that transforms raw restaurant data into actionable operational decisions.

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│            Next.js 15 + React + TypeScript                  │
│     Dashboard · Reports · Menu · Operations · Billing       │
└───────────────────────────┬─────────────────────────────────┘
                            │  HTTP / REST (JWT Bearer)
┌───────────────────────────▼─────────────────────────────────┐
│                         BACKEND                             │
│                  FastAPI + SQLAlchemy                       │
│   Auth · Reviews · Sales · Forecast · Alerts · Billing      │
└──────────┬────────────────┬────────────────┬────────────────┘
           │                │                │
    ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
    │  PostgreSQL │  │  AI Modules │  │  Scheduler  │
    │  Database   │  │   (Python)  │  │ APScheduler │
    └─────────────┘  └─────────────┘  └─────────────┘
```

---

## Data Flow

```
Operational Data (sales CSV)
          │
          ▼
   forecasting_engine.py
   (LinearRegression + fallback)
          │
          ▼
Customer Feedback (reviews CSV / text)
          │
          ▼
   review_analysis_model.py
   (keyword sentiment + topic extraction)
          │
          ▼
   correlation_engine_v2.py
   (LLM GPT-4o-mini or rule-based fallback)
          │
          ▼
   Operational Decisions
   (alerts, suggestions, daily report, email)
```

---

## Backend

### Stack
| Component | Technology |
|-----------|-----------|
| Framework | FastAPI 0.135 |
| ORM       | SQLAlchemy 2.0 |
| Database  | PostgreSQL (psycopg2-binary) |
| Auth      | JWT (python-jose + bcrypt) |
| Billing   | Stripe |
| Rate limiting | slowapi |
| Scheduler | APScheduler |
| AI / ML   | scikit-learn, OpenAI SDK |

### Module Structure

```
backend/
├── main.py              # App factory, middleware, scheduler setup
├── config.py            # Settings via pydantic-settings (.env)
├── api/                 # FastAPI routers (one per domain)
│   ├── auth.py
│   ├── health.py
│   ├── restaurants.py
│   ├── reviews.py
│   ├── analysis.py
│   ├── sales.py
│   ├── products.py
│   ├── forecast.py
│   ├── daily_report.py
│   ├── alerts.py
│   ├── correlations.py
│   ├── billing.py
│   ├── notifications.py
│   ├── integrations.py
│   ├── insights.py
│   ├── menu.py
│   ├── operations.py
│   └── organizations.py
├── services/            # Business logic (stateless, DB-aware)
│   ├── analysis_service.py
│   ├── forecast_service.py
│   ├── alert_service.py
│   ├── billing_service.py
│   ├── correlation_service.py
│   ├── daily_report_service.py
│   ├── email_service.py
│   ├── insights_service.py
│   ├── integration_service.py
│   ├── menu_service.py
│   ├── operations_service.py
│   ├── organization_service.py
│   ├── plan_service.py
│   ├── products_service.py
│   ├── review_analysis_service.py
│   ├── reviews_service.py
│   ├── sales_service.py
│   └── usage_service.py
├── auth/
│   ├── dependencies.py  # FastAPI dependency injection (get_current_user, get_owned_restaurant)
│   └── utils.py         # JWT create/verify, bcrypt hash/verify
└── db/
    ├── database.py      # SQLAlchemy engine + session
    └── models.py        # ORM models (all tables)
```

### Scheduled Jobs

| Time | Job | Description |
|------|-----|-------------|
| 02:00 daily | `_run_daily_forecasts` | Regenerate 7-day forecasts for all restaurants |
| 07:00 daily | `_run_daily_emails` | Send daily briefing email to active/trial users |
| 08:00 & 16:00 | `_run_alert_generation` | Detect alert conditions for all restaurants |
| Every 1 hour | `_run_integration_sync` | Sync all active third-party integrations |

---

## Frontend

### Stack
| Component | Technology |
|-----------|-----------|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| State | React Context (AuthContext) |
| HTTP | `fetch` (no external HTTP library) |

### Pages

| Route | Description |
|-------|-------------|
| `/` | Main dashboard: daily report, alerts, analysis, correlations |
| `/login` | Email/password authentication |
| `/register` | New user registration (7-day trial auto-started) |
| `/setup` | Restaurant creation and initial data upload |
| `/billing` | Subscription management (Stripe checkout) |
| `/insights` | AI-generated proactive insights |
| `/integrations` | Third-party integrations management |
| `/menu` | Menu optimization (2×2 matrix: popularity × revenue) |
| `/operations` | Purchase orders and staff planning |

### API Client (`app/lib/api.ts`)

Single typed API client module. Stores JWT token in `localStorage`. All authenticated requests attach `Authorization: Bearer <token>`.

---

## AI Modules

```
ai/
├── review_analysis_model.py    # Keyword sentiment + topic extraction
├── forecasting_engine.py       # LinearRegression + weighted avg fallback
├── forecasting_model.py        # Wrapper: runs engine + returns structured output
├── correlation_engine.py       # Rule-based: issue → operational suggestion
├── correlation_engine_v2.py    # LLM (GPT-4o-mini) + rule-based fallback
├── correlation_model.py        # Original English-based correlation model
├── alert_engine.py             # 5 alert detectors (stateless)
├── insights_engine.py          # Top-3 insights: predictive/diagnostic/prescriptive
├── menu_optimizer.py           # 2×2 menu matrix (popularity × revenue)
├── suggestions_engine.py       # Inventory + staffing + menu suggestions
└── llm_analysis.py             # LLM-based review analysis
```

See [`ai_modules.md`](ai_modules.md) for detailed documentation.

---

## Authentication & Multi-tenancy

- **JWT tokens**: 7-day expiry, stored client-side in `localStorage`
- **Resource isolation**: every API call validates that the authenticated user owns the requested restaurant (`get_owned_restaurant` dependency)
- **Organizations**: multi-restaurant support via `Organization` model (Phase 5)
- **Roles**: `admin` (default), supports extensible role field

---

## Subscription Plans

| Plan | Price | Features |
|------|-------|----------|
| Trial | Free (7 days) | All features |
| Starter | 49 €/month | Core features |
| Pro | 99 €/month | + Alerts, correlations |
| Premium | 199 €/month | Full feature set |

Feature gating is enforced server-side via `plan_service.require_feature()`.

---

## External Services

| Service | Purpose | Required |
|---------|---------|---------|
| PostgreSQL | Primary database | Yes |
| OpenAI (GPT-4o-mini) | LLM correlations + insights | Optional (fallback available) |
| Stripe | Billing and subscriptions | Optional (for payments) |
| SMTP server | Daily email briefings | Optional |

---

## Security

- Passwords hashed with `bcrypt`
- Rate limiting on login endpoint: 5 requests/minute per IP
- CORS restricted to `http://localhost:3000` (configure for production)
- Secrets managed via `.env` file (`pydantic-settings`)
