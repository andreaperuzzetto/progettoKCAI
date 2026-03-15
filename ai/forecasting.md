# Demand Forecasting Module

Goal:
Predict the number of orders per category for the next day.

Inputs:
- historical sales
- day of week
- reservations
- seasonality

Output:
{
  "pizza": 52,
  "pasta": 41,
  "burger": 18
}

Implementation guidance:
Start with a simple statistical model
(regression or Prophet).

Do not implement complex ML pipelines yet.

# Implementation Steps

1. Load sales data

Read historical sales data from the database
or uploaded CSV files.

2. Aggregate by product

Group sales data by:

- product
- date
- day of week.

3. Apply forecasting model

Use a simple statistical model such as:

- linear regression
- Prophet
- moving averages.

4. Return prediction

Generate predicted quantities for the next day.

Example output:

{
  "pizza": 52,
  "pasta": 41,
  "burger": 18
}