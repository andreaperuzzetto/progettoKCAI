# Product Assumptions

This document contains assumptions about the product,
users, and business context.

These assumptions guide product decisions during MVP development.

They may change as the product evolves.

---

# Restaurants Generate Usable Data

Most restaurants are assumed to have access to operational data such as:

- POS sales exports
- reservation data
- menu items

For the MVP, data will be imported using CSV files.

Future versions may integrate directly with POS systems.

---

# Restaurant Owners Prefer Simple Insights

Restaurant managers usually prefer:

- simple recommendations
- short reports
- clear actions

They rarely want complex dashboards or analytics tools.

Therefore the platform prioritizes:

- actionable insights
- minimal UI complexity
- short daily reports.

---

# Reviews Contain Operational Signals

Customer reviews are assumed to reflect real operational problems.

Common signals include:

- slow service
- burnt food
- long waiting times
- friendly staff

Repeated mentions across reviews can indicate structural issues.

---

# Operational Stress Causes Negative Reviews

Many negative reviews likely occur during peak workload.

Possible causes include:

- high number of customers
- insufficient staff
- overloaded kitchen equipment
- long preparation times

The system will attempt to detect these correlations.

---

# Forecasting Does Not Need Perfect Accuracy

Predictions do not need to be perfectly accurate.

Even moderately accurate forecasts can help restaurants:

- prepare ingredients
- anticipate busy periods
- reduce food waste.

The goal is **usefulness**, not perfect prediction.

---

# Restaurants May Adjust Operations

Restaurant managers are assumed to adjust operations if suggestions are:

- clear
- simple
- credible.

Examples:

- adding staff
- preparing ingredients earlier
- promoting high-performing menu items.