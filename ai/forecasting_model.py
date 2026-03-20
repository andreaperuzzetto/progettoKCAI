"""Demand forecasting module.

Stateless: receives structured sales data, returns predictions.
Does not access the database or persist any state.

Uses a weighted moving average with day-of-week adjustment.
"""

from datetime import date
from collections import defaultdict


def forecast_demand(
    sales: list[dict],
    target_date: date,
    window: int = 8,
) -> dict[str, int]:
    """Predict next-day demand per product.

    Args:
        sales: list of {"date": date, "product": str, "quantity": int}
        target_date: the date to forecast for
        window: number of recent data points per product to consider

    Returns:
        {"pizza": 52, "pasta": 41, ...}
    """
    if not sales:
        return {}

    target_dow = target_date.weekday()

    # Group quantities by product
    by_product: dict[str, list[dict]] = defaultdict(list)
    for row in sales:
        by_product[row["product"]].append(row)

    predictions: dict[str, int] = {}

    for product, rows in by_product.items():
        # Sort by date descending to pick recent entries
        rows.sort(key=lambda r: r["date"], reverse=True)
        recent = rows[:window]

        if not recent:
            continue

        # Weighted average: same day-of-week entries get weight 2, others weight 1
        total_weight = 0
        weighted_sum = 0.0
        for r in recent:
            w = 2 if r["date"].weekday() == target_dow else 1
            weighted_sum += r["quantity"] * w
            total_weight += w

        predictions[product] = round(weighted_sum / total_weight)

    return predictions
