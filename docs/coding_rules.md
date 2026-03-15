# Coding Rules

This document defines coding rules for the
Restaurant Intelligence Platform.

Its purpose is to ensure that all generated code
remains consistent with the project architecture
and MVP scope.

These rules should be followed for all implementations.

---

# General Principles

When writing code:

- prefer simple and readable solutions
- avoid unnecessary abstractions
- keep modules small and focused
- avoid introducing new frameworks or libraries unless necessary.

The goal is to maintain a clean and understandable codebase.

---

# MVP Scope Enforcement

Only implement functionality described in:

docs/mvp_scope.md

Do NOT introduce:

- advanced machine learning pipelines
- distributed systems
- real-time streaming systems
- complex microservices.

The MVP should remain simple.

---

# Backend Rules

Backend services must follow these principles.

Framework:

Python + FastAPI

Structure:

backend/
    api/
    db/
    services/

Responsibilities:

API routes

- handle HTTP requests
- validate inputs
- call service layer

Services

- implement business logic
- call AI modules
- orchestrate workflows

Database layer

- interact with PostgreSQL
- store and retrieve data.

---

# Database Rules

Database access must be centralized.

Only the backend database layer may:

- read from the database
- write to the database.

AI modules must NOT access the database directly.

All persistent state must be stored in PostgreSQL.

---

# AI Module Rules

AI modules must remain simple processing components.

They must be:

- stateless
- deterministic
- easy to test.

AI modules receive structured input and return structured output.

Example:

Input

sales data  
reviews

Output

forecast predictions  
correlation insights

AI modules must NOT:

- persist data
- open database connections
- manage background workers.

---

# Forecasting Rules

Forecasting models must remain simple.

Allowed approaches:

- linear regression
- moving averages
- Prophet

Do NOT implement:

- neural networks
- deep learning pipelines
- complex feature engineering.

The goal is to provide useful forecasts, not perfect predictions.

---

# Review Analysis Rules

Review analysis should focus on:

- sentiment classification
- topic extraction
- recurring complaint detection.

Avoid building complex NLP pipelines.

External language models may be used if needed.

---

# Correlation Engine Rules

The correlation engine should use simple logic.

Examples:

- anomaly detection
- rule-based correlations
- heuristic explanations.

Do NOT attempt:

- causal inference models
- complex statistical frameworks.

The goal is to produce **plausible operational explanations**.

---

# API Design Rules

APIs should remain simple and predictable.

Endpoints:

POST /upload-sales  
POST /upload-reviews  
GET /forecast  
GET /daily-report

Rules:

- validate inputs
- return structured JSON
- handle errors clearly.

---

# Code Quality

All code should aim to be:

- readable
- modular
- testable.

Avoid:

- deeply nested logic
- unnecessary abstractions
- large monolithic functions.

Functions should ideally remain under ~50 lines.

---

# Testing Rules

All modules should be testable.

Key areas to test:

- CSV ingestion
- forecasting logic
- review sentiment classification
- correlation engine outputs
- daily report generation.

Tests should verify expected behavior, not perfect accuracy.

---

# Future Extensions

Future features may include:

- ingredient demand forecasting
- staffing optimization
- supplier recommendations.

These features should NOT be implemented until explicitly added to the MVP scope.