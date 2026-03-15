# Technical Assumptions

This document contains assumptions related to
the technical implementation of the MVP.

---

# MVP Prioritizes Simplicity

The MVP should prioritize:

- simple models
- understandable logic
- clear outputs

Avoid complex machine learning pipelines.

---

# Forecasting Can Use Simple Models

Demand forecasting may use simple statistical approaches such as:

- linear regression
- moving averages
- Prophet

Deep learning models are not required for the MVP.

---

# Review Analysis Can Use Existing Language Models

Review sentiment and topic extraction can rely on:

- existing LLM APIs
- lightweight NLP models.

Custom NLP training is not required initially.

---

# Correlation Logic Starts With Heuristics

The correlation engine does not require causal inference models.

Initial implementations can use simple heuristics such as:

- detecting spikes in orders
- identifying repeated complaints
- comparing operational metrics across time.

More advanced methods may be added later.

---

# Example Data Will Be Used

Early development will rely on example datasets such as:

- sales_example.csv
- reviews_example.csv

These allow the system to be tested without real integrations.

---

# Data May Be Imperfect

Restaurant data may contain:

- missing values
- inconsistent product names
- incomplete records

The system should tolerate imperfect input data.

---

# Iterative Development Is Expected

The MVP will evolve through experimentation.

The development process should prioritize:

- small iterations
- testable modules
- fast feedback cycles.