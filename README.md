# Restaurant Intelligence Platform

An AI-powered SaaS platform that transforms restaurant operational data and customer reviews into daily operational decisions.

---

## What It Does

The platform connects three layers of restaurant intelligence:

```
Operational Data  (sales CSV)
        ↓
Customer Feedback  (reviews)
        ↓
Operational Decisions  (forecasts, alerts, suggestions, daily report)
```

Every morning at 07:00, restaurant owners receive an automated briefing:
> *"Tomorrow you'll have 85 covers (+30% vs average). Reviews show recurring slow service complaints. Add one waiter during the 19–22 shift. Here's your purchase order."*

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11 + FastAPI + SQLAlchemy |
| Database | PostgreSQL |
| Frontend | Next.js 15 + React + TypeScript + Tailwind CSS |
| AI / ML | scikit-learn + OpenAI GPT-4o-mini (optional) |
| Billing | Stripe |
| Auth | JWT (python-jose + bcrypt) |
| Scheduler | APScheduler |

---

## Key Features

- 📊 **Sales data import** via CSV upload
- 💬 **Review sentiment analysis** with topic extraction
- 📈 **7-day demand forecasting** (LinearRegression + fallback)
- 📋 **Daily operational report** (dashboard + email at 07:00)
- 🔔 **Smart alerts** — high demand, sales drops, negative review spikes
- 🔗 **Causal correlations** — rule-based + optional LLM (GPT-4o-mini)
- 🍽️ **Menu optimization** — 2×2 popularity × revenue matrix
- 🛒 **Purchase order generation** — based on forecast × ingredients
- 👥 **Staff planning** — daily shift recommendations
- 💡 **AI insights** — top-3 predictive/diagnostic/prescriptive insights
- 💳 **Subscription plans** — Starter (49€) / Pro (99€) / Premium (199€)
- 🏢 **Multi-tenant organizations** — restaurant chains support

---

## Project Structure

```
progettoKCAI/
├── backend/
│   ├── api/          # FastAPI routers
│   ├── services/     # Business logic
│   ├── auth/         # JWT auth utilities
│   ├── db/           # ORM models + database session
│   ├── migrations/   # SQL migration files
│   ├── tests/        # pytest test suite
│   ├── main.py       # App factory + scheduler setup
│   ├── config.py     # Settings (pydantic-settings + .env)
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── lib/      # API client (api.ts) + auth context
│   │   ├── components/  # Nav, providers
│   │   └── [pages]/  # Dashboard, login, register, billing, menu, operations, insights
│   ├── package.json
│   └── next.config.ts
├── ai/               # Stateless AI/ML modules
│   ├── review_analysis_model.py
│   ├── forecasting_engine.py
│   ├── correlation_engine.py
│   ├── correlation_engine_v2.py
│   ├── alert_engine.py
│   ├── insights_engine.py
│   ├── menu_optimizer.py
│   └── suggestions_engine.py
├── docs/             # Project documentation
├── examples/         # Sample CSV datasets
└── CLAUDE.md         # Development guidelines
```

---

## Quick Start

### Prerequisites
- Python ≥ 3.11
- Node.js ≥ 18
- PostgreSQL ≥ 14 **or** a [Supabase](https://supabase.com) project

### Backend

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp .env.example .env   # then edit .env

# If using local PostgreSQL (skip for Supabase)
createdb kcai

# Start the API server
uvicorn backend.main:app --reload
```

API available at: `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App available at: `http://localhost:3000`

---

## Environment Variables

Create a `.env` file in the project root (use `.env.example` as template):

```bash
cp .env.example .env
```

```env
# Required — choose one:
# Local PostgreSQL:
DATABASE_URL=postgresql://user:password@localhost:5432/kcai
# Supabase (Session pooler, port 5432):
# DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres

SECRET_KEY=your-secret-key-min-32-chars

# Optional: enables LLM-powered correlations and insights
OPENAI_API_KEY=sk-...

# Optional: enables billing
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_STARTER=price_...
STRIPE_PRICE_ID_PRO=price_...
STRIPE_PRICE_ID_PREMIUM=price_...

# Optional: enables daily email briefings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourdomain.com
```

---

## Sample Data

The `examples/` directory contains CSV datasets for testing:

**Sales format** (`examples/sales_example.csv`):
```csv
date,product,quantity
2025-01-01,pizza,45
2025-01-01,pasta,30
```

**Reviews format** (`examples/reviews_example.csv`):
```csv
date,platform,review_text,rating
2025-01-01,google,"Great pizza and friendly staff",5
2025-01-02,tripadvisor,"Good pasta but slow service",3
```

---

## Running Tests

```bash
pytest backend/tests/ -v
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/supabase.md](docs/supabase.md) | **Supabase setup guide** (connection string, pooler, troubleshooting) |
| [docs/architecture.md](docs/architecture.md) | System architecture, module structure, scheduled jobs |
| [docs/api_reference.md](docs/api_reference.md) | Full REST API reference with request/response examples |
| [docs/data_model.md](docs/data_model.md) | Database schema, all tables and columns |
| [docs/ai_modules.md](docs/ai_modules.md) | AI/ML modules: algorithms, inputs, outputs |
| [docs/deployment.md](docs/deployment.md) | Deployment guide (local + production) |
| [docs/product_vision.md](docs/product_vision.md) | Product vision and strategic pillars |
| [docs/mvp_scope.md](docs/mvp_scope.md) | MVP scope, feature flags by plan |
| [docs/assumptions_product.md](docs/assumptions_product.md) | Product assumptions and risks |
| [docs/assumptions_technical.md](docs/assumptions_technical.md) | Technical assumptions and scaling thresholds |

---

## Subscription Plans

| Plan | Price | Key Features |
|------|-------|-------------|
| Trial | Free (7 days) | All features |
| Starter | 49 €/month | Forecasting, daily report, analysis |
| Pro | 99 €/month | + Alerts, LLM correlations, menu optimizer, operations |
| Premium | 199 €/month | + Integrations, organizations |

---

## License

Private — all rights reserved.