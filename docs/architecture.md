# System Architecture

This document describes the initial architecture
of the Restaurant Intelligence Platform.

The architecture prioritizes:

- simplicity
- modularity
- rapid iteration.

---

# High Level Components

Frontend  
Dashboard interface

Backend API  
Handles data ingestion and business logic

AI Engine  
Processes forecasting and review analysis

Database  
Stores restaurant data

---

# Repository Structure

backend/
API routes and data storage

ai/
forecasting
review analysis
correlation engine

frontend/
dashboard UI

docs/
project documentation

---

# Architecture Overview

Frontend (Next.js)

↓

Backend API (FastAPI)

↓

Database (PostgreSQL)

↓

AI Services (Python)

---

# Frontend

Technology:

Next.js  
React  
Tailwind CSS

Responsibilities:

- display dashboard
- upload CSV files
- show reports and insights.

---

# Backend

Technology:

Python  
FastAPI

Responsibilities:

- handle API requests
- process uploaded data
- trigger AI analysis
- generate reports.

Key endpoints:

/upload-sales  
/upload-reviews  
/forecast  
/daily-report

---

# Data Access Layer

The backend is responsible for all database access.

AI modules should not read or write directly to the database.

Instead, the backend provides data to AI modules through
well-defined function calls or API endpoints.

This ensures:

- clear separation of responsibilities
- easier testing
- simpler system architecture.

Example flow:

Backend reads sales data from the database

↓

Backend sends structured data to the forecasting module

↓

AI module returns prediction results

↓

Backend stores results in the database

---

# AI Engine

AI modules run as Python services.

Modules:

Demand Forecasting  
Review Analysis  
Correlation Engine

These modules analyze data and return structured insights.

---

# Database

Technology:

PostgreSQL

Stores:

- sales data
- reviews
- forecasts
- generated reports.

---

# Data Flow

1 Upload sales data  
2 Store in database  
3 Run forecasting model  
4 Analyze reviews  
5 Detect correlations  
6 Generate daily report.

---

# MVP Constraints

The system should remain simple.

Avoid:

- distributed systems
- microservice complexity
- event streaming
- advanced ML pipelines.

These may be introduced later if needed.