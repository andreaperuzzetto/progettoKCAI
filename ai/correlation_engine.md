# Correlation Strategy

The correlation engine links customer complaints
with operational signals.

Steps:

1. Extract complaint topics from reviews

Identify recurring complaint themes such as:

- slow service
- burnt food
- long waiting time

2. Aggregate operational data for the same period

Collect operational metrics during the time window of the complaints.

Examples:

- number of orders
- kitchen load
- staffing level
- preparation time

3. Look for anomalies

Detect unusual operational patterns such as:

- order spikes
- staff shortages
- kitchen overload

4. Generate hypothesis

Produce a possible explanation linking operations and complaints.

Example output:

problem: pizza burnt  
possible_cause: oven overload during peak hours  
suggested_action: reduce simultaneous pizza orders or add kitchen capacity