# Data Model

This document defines the initial data structure
for the Restaurant Intelligence Platform.

The schema is intentionally simple for the MVP.

---

# Entities

Restaurant  
Sales  
Reviews  
Forecast  
DailyReport

---

# Restaurant

Represents a single restaurant using the platform.

Fields:

id  
name  
location  
created_at

---

# Sales

Represents historical sales data.

Fields:

id: UUID  
restaurant_id: UUID  
date: DATE  
product: TEXT  
quantity: INTEGER

Example:

date: 2025-01-01  
product: pizza  
quantity: 45

---

# Reviews

Represents customer reviews collected from platforms.

Fields:

id: UUID
restaurant_id: UUID
date: DATE
platform: TEXT
review_text: TEXT
sentiment: TEXT

Sentiment values:

positive  
neutral  
negative

---

# Forecast

Stores predicted sales for the next day.

Fields:

id  
restaurant_id  
date  
product  
predicted_quantity

Example:

date: 2025-02-01  
product: pizza  
predicted_quantity: 52

---

# DailyReport

Stores the generated daily operational report.

Fields:

id  
restaurant_id  
date  
forecast_summary  
issues  
suggestions

Example:

issues:
- slow service weekend

suggestions:
- add one waiter Saturday evening.

---

# Relationships

Restaurant

↓  

Sales  
Reviews  
Forecast  
DailyReport

Each dataset is linked through restaurant_id.

---

# MVP Simplifications

For the MVP:

- products are stored as simple text
- menu categories are not required
- ingredient tracking is not included.

These features may be added later.

---

# Future Extensions

Possible future tables:

MenuItems  
Ingredients  
KitchenMetrics  
Staffing  
Suppliers