# Development Tasks

This document defines the development roadmap for the
Restaurant Intelligence Platform MVP.

The goal is to break development into small, clear tasks
that can be implemented incrementally.

Each task should produce working, testable code.

---

# Development Principles

Follow these rules when implementing tasks:

- implement tasks in order
- keep implementations simple
- do not introduce features outside the MVP scope
- reuse existing modules where possible
- prefer readability over complexity.

If a task is unclear, refer to:

docs/mvp_scope.md  
docs/system_flow.md  
docs/architecture.md

---

# Phase 1 — Project Setup

Goal: create the basic project structure.

Tasks:

1. Initialize repository structure

Create folders:

backend/  
frontend/  
ai/  
docs/

2. Setup backend service

Create a FastAPI application inside:

backend/

Include:

- base FastAPI app
- health endpoint `/health`

3. Setup database connection

Configure PostgreSQL connection.

Create database access module inside:

backend/db/

Responsibilities:

- connect to database
- execute queries
- manage models.

---

# Phase 2 — Database Models

Goal: implement database schema.

Reference:

docs/data_model.md

Tasks:

1. Implement Restaurant model

Fields:

id  
name  
location  
created_at

2. Implement Sales model

Fields:

id  
restaurant_id  
date  
product  
quantity

3. Implement Reviews model

Fields:

id  
restaurant_id  
date  
platform  
review_text  
sentiment

4. Implement Forecast model

Fields:

id  
restaurant_id  
date  
product  
predicted_quantity

5. Implement DailyReport model

Fields:

id  
restaurant_id  
date  
forecast_summary  
issues  
suggestions

---

# Phase 3 — Sales Data Ingestion

Goal: allow restaurants to upload sales data.

Reference:

docs/system_flow.md

Tasks:

1. Implement endpoint

POST /upload-sales

Input:

CSV file

Structure:

date,product,quantity

2. Parse CSV file

Convert rows into structured records.

3. Store records in Sales table.

4. Validate input data

Check:

- required fields
- valid dates
- numeric quantities.

---

# Phase 4 — Review Data Input

Goal: ingest customer reviews.

Tasks:

1. Implement endpoint

POST /upload-reviews

Input:

CSV file or JSON payload.

Fields:

date  
platform  
review_text

2. Store reviews in Reviews table.

3. Prepare reviews for sentiment analysis.

---

# Phase 5 — Demand Forecast Module

Goal: implement the forecasting engine.

Reference:

ai/forecasting.md

Tasks:

1. Load sales data

Query historical sales from database.

2. Aggregate sales

Group by:

product  
date  
day of week

3. Apply forecasting method

Use a simple statistical model such as:

- linear regression
- moving averages
- Prophet

4. Return predicted values

Example:

{
  "pizza": 52,
  "pasta": 41,
  "burger": 18
}

5. Store predictions in Forecast table.

---

# Phase 6 — Review Analysis Module

Goal: analyze customer feedback.

Tasks:

1. Implement sentiment classification

Classify reviews as:

positive  
neutral  
negative

2. Extract common complaint topics.

Examples:

- slow service
- burnt food
- long waiting time

3. Store extracted insights.

---

# Phase 7 — Correlation Engine

Goal: connect reviews with operational signals.

Reference:

ai/correlation_engine.md

Tasks:

1. Identify recurring complaint topics.

2. Retrieve operational data for the same time period.

Sources:

Sales  
Forecast

3. Detect anomalies.

Examples:

- order spikes
- staff shortages
- kitchen overload

4. Generate hypothesis.

Example output:

problem: burnt pizza  
possible_cause: oven overload  
suggested_action: reduce simultaneous pizza orders.

---

# Phase 8 — Daily Report Generator

Goal: generate operational insights.

Tasks:

1. Retrieve forecast results.

2. Retrieve review insights.

3. Retrieve correlation analysis.

4. Generate report summary.

Example:

Forecast

Pizza: 52  
Pasta: 41

Issues

Slow service during weekends

Suggestions

Add one waiter on Saturday evenings.

5. Store results in DailyReport table.

---

# Phase 9 — Dashboard MVP

Goal: provide minimal frontend interface.

Reference:

docs/mvp_scope.md

Tasks:

Create dashboard pages:

Today  
Problems  
Opportunities

Display:

- forecast results
- detected issues
- operational suggestions.

---

# Phase 10 — Integration Test

Goal: validate end-to-end workflow.

Test scenario:

1. Upload sales data
2. Upload reviews
3. Run forecast
4. Run correlation engine
5. Generate daily report

Verify:

- correct data storage
- correct predictions
- correct suggestions.

---

# Out of Scope

The following features must NOT be implemented in the MVP:

- POS integrations
- real-time analytics
- advanced ML pipelines
- automated purchasing systems
- multi-restaurant management.

These may be implemented in later versions.

---

# Future Development

Possible future tasks:

- ingredient demand prediction
- staffing optimization
- supplier recommendations
- real-time kitchen monitoring
- menu optimization.