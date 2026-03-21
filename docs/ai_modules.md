# AI Modules — Restaurant Intelligence Platform

All AI modules are **stateless Python functions** in the `ai/` directory. They receive data as arguments and return structured results. They do not directly access the database — that is the responsibility of the service layer.

---

## 1. Review Analysis (`review_analysis_model.py`)

**Purpose:** Classify sentiment and extract complaint topics from review texts using keyword heuristics.

### Input
```python
reviews: list[dict]  # [{"review_text": "..."}, ...]
```

### Output
```python
[{"review_text": "...", "sentiment": "positive|negative|neutral", "topics": [...]}]
```

### How It Works

**Sentiment classification** — keyword matching:
- Positive words: `great`, `excellent`, `delicious`, `fresh`, `recommended`, etc.
- Negative words: `bad`, `slow`, `burnt`, `dirty`, `overpriced`, etc.
- Rule: `pos > neg → positive`, `neg > pos → negative`, else `neutral`

**Topic extraction** — phrase matching against 9 complaint categories:
| Topic | Example keywords |
|-------|-----------------|
| `slow service` | "slow waiter", "waited too long" |
| `burnt food` | "burnt", "overcooked", "charred" |
| `cold food` | "cold pizza", "lukewarm" |
| `long waiting time` | "waiting time", "took forever" |
| `rude staff` | "rude", "unfriendly", "impolite" |
| `dirty environment` | "dirty", "unclean", "filthy" |
| `overpriced` | "too expensive", "not worth the price" |
| `raw food` | "raw", "undercooked" |
| `small portions` | "small portion", "tiny portion" |

**Topic frequency summary:**
```python
summarize_topics(analyzed) → {"slow service": 8, "burnt food": 3}
```

### Limitations
- English keywords only (v1). Italian support is in `correlation_engine.py` rules.
- No semantic understanding; easily fooled by negations ("not slow").
- Designed to be replaced with an LLM-based module.

---

## 2. Forecasting Engine (`forecasting_engine.py`)

**Purpose:** Predict daily demand (covers and per-product quantities) for the next 7 days.

### Input
```python
sales: list[dict]  # [{"date": date, "product_name": str, "quantity": int}]
horizon_days: int = 7
```

### Output
```python
[
    {
        "date": date,
        "expected_covers": int,
        "product_predictions": {"pizza": 42, "pasta": 28, ...}
    },
    ...  # 7 entries
]
```

### Algorithm

**Feature engineering** (per training sample):
- `day_of_week` (0 = Monday, 6 = Sunday)
- `is_weekend` (binary)
- `rolling_7d_avg` (average of previous 7 days)
- `rolling_14d_avg` (average of previous 14 days)
- `same_weekday_avg_4w` (average of same weekday in last 4 weeks)

**Model:** `sklearn.linear_model.LinearRegression` trained separately for:
1. Total daily covers (sum of all products)
2. Each individual product

**Fallback** (< 7 data points):
- Simple exponentially weighted moving average
- Formula: `pred = 0.6 × weighted_avg + 0.4 × same_weekday_avg`

**Minimum guaranteed output:** Returns zeros if no sales data is available.

---

## 3. Correlation Engine v1 (`correlation_engine.py`)

**Purpose:** Rule-based mapping from review issues to operational suggestions.

### Input
```python
issues: list[dict]        # [{"name": "servizio lento", "frequency": 8}]
forecast_tomorrow: dict   # {"expected_covers": 85, "product_predictions": {...}}
```

### Output
```python
[{"type": "staffing", "message": "...", "priority": "high", "source": "correlation", "issue": "..."}]
```

### Rules (7 total)

| Issue keywords | Condition | Suggestion type |
|---------------|-----------|----------------|
| servizio lento, attesa | Any covers > 0 | staffing |
| piatti freddi, temperatura | Covers ≥ 30 | kitchen |
| porzione piccola | Always | menu |
| prezzo, caro | Covers < 20 | menu |
| pulizia, sporco | Always | operations |
| rumore, musica alta | Covers ≥ 40 | ambiance |
| parcheggio, accesso | Covers ≥ 40 | logistics |

Suggestions are sorted by priority: `high → medium → low`.

---

## 4. Correlation Engine v2 (`correlation_engine_v2.py`)

**Purpose:** LLM-based causal correlation analysis with graceful fallback.

### Input
```python
sales: list[dict]
forecast_tomorrow: dict
issues: list[dict]
avg_covers: float
api_key: str = ""
```

### Output
```python
[
    {
        "cause": "personale insufficiente nelle ore di punta",
        "confidence": 0.85,
        "suggestion": "Aggiungi 1-2 camerieri nelle fasce 19-22.",
        "impact_level": "high"
    }
]
```

### How It Works

1. **Context building:** Summarizes last 7 vs previous 7 days sales trend, top products, tomorrow's forecast, and review issues into a compact text block.
2. **LLM call:** Sends to `gpt-4o-mini` with a structured system prompt requesting JSON output.
3. **Post-processing:** Filters out correlations with `confidence < 0.6`, caps at 5, sorts by impact.
4. **Rule-based fallback:** If no API key or LLM fails, applies 3 deterministic rules (service speed, food temperature, cleanliness).

### System Prompt Strategy
- Forces structured JSON response
- Limits to 5 results with confidence ≥ 0.6
- Temperature = 0.3 (deterministic/consistent)
- Italian language output

---

## 5. Alert Engine (`alert_engine.py`)

**Purpose:** Detect 5 types of operational alert conditions.

### Alert Types

| Type | Detector | Trigger condition |
|------|---------|-----------------|
| `high_demand` | `detect_high_demand` | Tomorrow's covers ≥ 130% of historical average |
| `negative_spike` | `detect_negative_review_spike` | Negative sentiment increased by ≥ 15 percentage points |
| `sales_drop` | `detect_sales_anomaly` | Last 3 days daily avg dropped ≥ 30% vs previous 7 days |
| `low_sentiment` | `detect_low_sentiment` | Positive sentiment < 40% |
| `issue_increase` | `detect_issue_increase` | Any issue frequency increased by ≥ 2 |

### Severity Escalation
- `high_demand`: `high` if +50%, else `medium`
- `sales_drop`: `high` if -50%, else `medium`
- `low_sentiment`: `high` if < 25%, else `medium`

### Main Entry Point
```python
run_all_detections(forecast, historical_sales, avg_historical_covers, analysis_now, analysis_prev)
→ list[AlertDict]
```

---

## 6. Insights Engine (`insights_engine.py`)

**Purpose:** Generate top-3 proactive insights ranked by `confidence × impact`.

### Insight Types
- **`predictive`** — "Tomorrow there's a risk of kitchen overload"
- **`diagnostic`** — "Sales drop caused by slow service"
- **`prescriptive`** — "Add 1 waiter during 19–22 shift"

### Ranking Formula
```
score = confidence × impact
```

Returns top 3 sorted by descending score.

### LLM Mode (if `api_key` provided)
Sends sales delta, avg covers, tomorrow's forecast, and top issues to `gpt-4o-mini` for 3 concrete Italian-language insights.

### Rule-based Fallback (4 rules)
1. Sales dropped > 30% → `diagnostic` (links to top issue)
2. Tomorrow covers > 130% of avg → `predictive` (overload risk)
3. Recurring service issues → `prescriptive` (add staff)
4. Kitchen/food quality issues → `prescriptive` (reduce backlog)

---

## 7. Menu Optimizer (`menu_optimizer.py`)

**Purpose:** Classify menu items using a 2×2 matrix and suggest actions.

### 2×2 Matrix

```
         │  HIGH REVENUE  │  LOW REVENUE
─────────┼────────────────┼──────────────
HIGH POP │   PROMOTE ⭐   │  OPTIMIZE 💰
─────────┼────────────────┼──────────────
LOW POP  │  REPOSITION 💎 │  REMOVE/MONITOR 🔻
```

### Actions
| Action | Trigger | Priority |
|--------|---------|---------|
| `promote` | high pop + high revenue | high |
| `optimize_price` | high pop + low revenue | high |
| `reposition` | low pop + high revenue | medium |
| `remove` | low pop + low revenue + trend < -10% | low |
| `monitor` | low pop + low revenue + stable | low |

### Normalization
Popularity and revenue scores are min-max normalized to [0, 1] across the restaurant's entire menu.

---

## 8. Suggestions Engine (`suggestions_engine.py`)

**Purpose:** Generate combined inventory, staffing, and menu suggestions.

### Three Sub-generators

**Inventory suggestions (`generate_inventory_suggestions`)**
- Aggregates forecast demand over 7 days
- Multiplies by `quantity_per_unit` from product-ingredient mappings
- Outputs: "Prepare X kg of Farina for the next 7 days"

**Staffing suggestions (`generate_staffing_suggestions`)**
- Compares tomorrow's forecast to historical avg covers
- `ratio ≥ 1.3` → "Consider extra staff" (priority: high)
- `ratio ≤ 0.7` → "Possible staff reduction" (priority: medium)

**Menu trend suggestions (`generate_menu_suggestions`)**
- Compares last 7 days vs previous 7 days per product
- Growth ≥ +30% → "Ensure availability" (priority: medium)
- Drop ≥ -30% → "Consider promotion" (priority: low)

### Output
All three are combined and sorted by priority (`high → medium → low`). Returns top 5 menu trend suggestions.

---

## LLM Integration Summary

| Module | LLM Model | Fallback |
|--------|-----------|---------|
| `correlation_engine_v2.py` | `gpt-4o-mini` | Rule-based (3 rules) |
| `insights_engine.py` | `gpt-4o-mini` | Rule-based (4 rules) |
| `llm_analysis.py` | `gpt-4o-mini` | N/A |

All LLM calls use `temperature=0.3` and `response_format={"type": "json_object"}` for consistency.

---

## Design Principles

1. **Stateless** — modules receive data, return results, no side effects
2. **Graceful degradation** — every LLM-dependent module has a rule-based fallback
3. **Italian output** — all user-facing messages are in Italian
4. **Composable** — modules can be called independently or chained
5. **Replaceable** — each module has a clear interface designed for future replacement with better models
