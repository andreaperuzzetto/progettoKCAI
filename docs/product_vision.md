# Product Vision — Restaurant Intelligence Platform

## The Problem

Restaurants generate enormous amounts of operational data every day:
- Sales records, product quantities, revenue
- Customer reviews across multiple platforms
- Staff schedules, inventory levels, supplier orders

Yet **most restaurants don't use this data effectively**. Owners and managers are overwhelmed by operations and lack the tools — or time — to extract insights from the data they already have.

The result: decisions are made on gut feeling rather than evidence. Problems are discovered too late. Opportunities are missed.

---

## The Vision

**An AI operational advisor that sits alongside every restaurant owner.**

The platform bridges three layers of restaurant intelligence:

```
Operational Data  (sales, products, inventory)
        ↓
Customer Feedback  (reviews, sentiment, complaints)
        ↓
Operational Decisions  (forecasts, alerts, staff plans, purchase orders)
```

Instead of dashboards that require interpretation, the platform delivers **specific, actionable recommendations** — every day, automatically.

---

## Core Value Proposition

> "Tomorrow you'll have 85 covers (+30% vs average). Reviews show a recurring problem with slow service.
> Add one waiter during the 19–22 shift. Here's your ingredient purchase order."

This is what every restaurant owner needs to hear each morning.

---

## Target Users

**Primary:** Independent restaurant owners and managers (1–3 locations)
- Pain point: no time for data analysis, need practical daily guidance
- Value: daily operational report, demand forecasts, review monitoring

**Secondary:** Restaurant chains and groups (via Organizations feature)
- Pain point: aggregating data across multiple locations
- Value: centralized dashboard, market benchmarking by city/category

---

## Strategic Pillars

### 1. Simplicity First
Every feature must be understandable without training. The daily report is the primary touchpoint — one screen, one decision.

### 2. Actionability
Every insight must include a specific action. "Your reviews are getting worse" is not enough. "Your reviews show a 15% increase in complaints about slow service — consider adding staff on Friday evenings" is.

### 3. Graceful Intelligence
LLM features (GPT-4o-mini) enhance the experience when available, but the system works without them. Rule-based fallbacks ensure reliability even without API keys.

### 4. Progressive Discovery
Start with the MVP. Learn from real usage. Add features only when validated by actual restaurant owners.

---

## Product Evolution

| Phase | Focus | Status |
|-------|-------|--------|
| 1–2 | Core auth, reviews import, sentiment analysis | ✅ Done |
| 3 | Sales data, forecasting, daily report | ✅ Done |
| 4 | Alerts, correlations (rule-based + LLM), integrations | ✅ Done |
| 5 | Menu optimizer, operations (purchase orders + staff), organizations, insights | ✅ Done |
| 6 | Mobile app, real-time sync, market benchmarking | 🔜 Future |

---

## Success Metrics

The platform succeeds when restaurant owners:
1. Open the daily report every morning before service
2. Act on at least one suggestion per week
3. Report fewer operational surprises (unexpected demand spikes, running out of ingredients)
4. See measurable improvement in review sentiment over time

---

## Guiding Principles

- **Build less, but build it right** — MVP first, complexity only when proven
- **Restaurant owners are not data scientists** — plain Italian, no jargon
- **Reliability > sophistication** — a wrong LLM answer is worse than no answer
- **Ownership** — each restaurant's data is strictly isolated and belongs to the owner
