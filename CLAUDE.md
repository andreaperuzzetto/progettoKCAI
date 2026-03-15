# CLAUDE.md

## Project

Restaurant Intelligence Platform

An AI system that transforms restaurant operational data and customer reviews
into daily operational decisions.

The goal of this project is **not to build a complete production system immediately**.

Instead, the objective is to:

- build an MVP
- test the workflow
- learn from real usage
- iteratively evolve the product.

---

# Development Philosophy

This project should evolve **incrementally**.

Prefer:

- simple solutions
- readable code
- modular services
- small iterations

Avoid:

- premature optimization
- unnecessary complexity
- building features outside the MVP scope.

---

# Core Product Idea

Restaurants generate data but rarely use it effectively.

This platform connects three layers:

Operational Data  
↓  
Customer Feedback  
↓  
Operational Decisions

The system acts as an **AI operational advisor**.

---

# Main MVP Capabilities

The MVP should support:

1. Uploading restaurant sales data
2. Importing customer reviews
3. Detecting sentiment and recurring complaints
4. Forecasting next-day demand
5. Generating a daily operational report

---

# Context Files

Claude should read these files before implementing features.

Product vision:
docs/product_vision.md

MVP scope:
docs/mvp_scope.md

System architecture:
docs/architecture.md

Data model:
docs/data_model.md

Assumptions:
docs/assumptions_product.md
docs/assumptions_technical.md

AI modules:
ai/forecasting.md  
ai/review_analysis.md  
ai/correlation_engine.md

Example datasets:
examples/

## Context Priority

When implementing features read files in this order:

1. docs/mvp_scope.md
2. docs/data_model.md
3. docs/architecture.md
4. ai/*
5. docs/assumptions.md

Only read other files if necessary.

---

# Working Rules

When implementing code:

1. Keep modules small and composable.
2. Prefer clarity over cleverness.
3. Document assumptions in `docs/assumptions.md`.
4. Use example datasets for testing.
5. Build only what is required for the MVP.

---

# Coding Guidelines

Backend:
Python + FastAPI

Frontend:
Next.js + React

Database:
PostgreSQL

AI modules:
Python services

All services should expose **clear APIs**.

---

# If Requirements Are Unclear

If a feature is not defined in the MVP scope:

- ask for clarification
- do not invent complex solutions.

The goal is **progressive discovery**, not perfect design.