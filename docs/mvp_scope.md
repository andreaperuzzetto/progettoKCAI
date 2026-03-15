# MVP Scope

The MVP should answer one simple question:

"What should the restaurant prepare tomorrow?"

The system should provide daily operational insight
based on sales data and customer reviews.

---

# Core Features

## 1 Sales Data Upload

Restaurants can upload a CSV file containing historical sales.

Example structure:

date,product,quantity
2025-01-01,pizza,45
2025-01-01,pasta,31
2025-01-01,burger,12

The system stores this data for analysis.

---

## 2 Customer Review Import

The system should accept reviews via:

- CSV upload
- manual input

Example structure:

date,platform,review

The system will analyze:

- sentiment
- recurring topics
- common complaints.

---

## 3 Sentiment Analysis

Reviews should be classified into:

- positive
- neutral
- negative

The system should also detect recurring themes such as:

- slow service
- burnt food
- long waiting times.

---

## 4 Demand Forecast

Using historical sales, the system should predict
next-day demand for each product category.

Example output:

Pizza: 52  
Pasta: 41  
Burger: 18

The model does not need to be highly sophisticated.

---

## 5 Daily Operational Report

The system should generate a simple report.

Example:

Forecast

Pizza: 52  
Pasta: 41

Issues

Slow service on weekends.

Suggestions

Add one waiter on Saturday evenings.

---

# User Flow

The MVP should follow this operational flow.

User uploads sales data

↓

User uploads reviews

↓

System runs demand forecast

↓

System analyzes reviews

↓

System generates daily operational report

---

# Data Retention

For the MVP the system only needs to keep recent historical data.

Sales data retention:

Keep the last 12 months of sales data.

Older data may be archived or ignored by forecasting models.

Reason:

- restaurants change menus frequently
- older data may become irrelevant
- limiting the dataset simplifies forecasting models.

---

# User Interface

The MVP UI should be simple.

Main sections:

Today  
Problems  
Opportunities

---

# What The MVP Should NOT Include

The MVP should NOT include:

- POS integrations
- real-time analytics
- advanced machine learning
- complex dashboards
- automated purchasing systems.

These may be explored later.

---

# MVP Success Criteria

The MVP is successful if it can:

- process sales data
- analyze reviews
- generate useful operational suggestions.

Accuracy is less important than **usefulness**.