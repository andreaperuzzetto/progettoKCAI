# System Flow

This document describes the operational flow of the
Restaurant Intelligence Platform MVP.

Its purpose is to clarify how data moves through the system
and how different modules interact.

The goal is to avoid architectural ambiguity during development.

---

# High-Level Flow

The system follows a simple pipeline.

Sales Data  
+  
Customer Reviews  

↓

Data Storage

↓

AI Analysis

↓

Daily Operational Report

---

# Detailed Flow

## Step 1 — Sales Data Upload

The restaurant uploads historical sales data using a CSV file.

Example structure:

date,product,quantity

The backend:

1. validates the file
2. parses the rows
3. stores the data in the Sales table.

Database table used:

Sales

---

## Step 2 — Review Data Input

Customer reviews are imported into the system.

Input methods:

- CSV upload
- manual entry

Example structure:

date,platform,review_text

The backend stores the data in:

Reviews table.

---

## Step 3 — Data Storage

All uploaded data is stored in PostgreSQL.

Tables involved:

Sales  
Reviews

This stored data becomes the input for AI modules.

---

# AI Processing Pipeline

Once data is available, the system runs AI analysis.

Modules involved:

Demand Forecasting  
Review Analysis  
Correlation Engine

---

# Stateless AI Modules

AI modules are designed as stateless processing components.

This means they do not store persistent state or internal memory.

They receive input data, process it, and return results.

Example:

Input:

sales data  
reviews

↓

AI module processes the data

↓

Output:

forecast results  
correlation insights

All persistent data is stored in the database by the backend.

Benefits:

- simpler architecture
- easier debugging
- easier scaling
- predictable behavior.

---

## Step 4 — Demand Forecast

The forecasting module predicts next-day demand.

Input:

Sales data

Process:

1. aggregate sales history
2. detect day-of-week patterns
3. generate predicted quantities

Output example:

Pizza: 52  
Pasta: 41  
Burger: 18

Results are stored in:

Forecast table.

---

## Step 5 — Review Analysis

The review analysis module processes customer feedback.

Input:

Reviews table.

Process:

1. classify sentiment
2. extract recurring topics
3. detect negative patterns.

Example topics:

- slow service
- burnt food
- long waiting time.

---

## Step 6 — Correlation Engine

The correlation engine connects reviews and operational data.

Inputs:

Sales  
Forecast  
Reviews

Process:

1. detect complaint topics
2. identify operational anomalies
3. generate possible explanations.

Example output:

problem: burnt pizza  
possible_cause: oven overload  
suggested_action: reduce simultaneous pizza orders

---

# Step 7 — Daily Report Generation

The backend generates a daily operational report.

The report combines:

Forecast results  
Review insights  
Correlation analysis.

Example report:

Forecast

Pizza: 52  
Pasta: 41

Issues

Slow service on weekends

Suggestions

Add one waiter Saturday evening.

---

# API Interaction Flow

Typical system interaction:

1. POST /upload-sales
2. POST /upload-reviews
3. GET /forecast
4. GET /daily-report

---

# Component Responsibilities

Frontend

- display dashboard
- upload files
- show reports.

Backend

- store data
- orchestrate analysis
- expose APIs.

AI Modules

- forecast demand
- analyze reviews
- detect correlations.

Database

- persist all data
- store predictions and reports.

---

# MVP Constraints

The system should remain simple.

Avoid:

- real-time pipelines
- streaming architectures
- distributed services
- complex ML orchestration.

The MVP is designed for **clarity and iteration**.

---

# Future Extensions (Not in MVP)

Possible future capabilities:

- POS integrations
- automated ingredient recommendations
- staff optimization
- real-time operational alerts
- supplier optimization.

These are intentionally excluded from the MVP.