"""
Forecasting engine for daily sales prediction.

Strategy:
  - Feature engineering: day_of_week, is_weekend, rolling 7-day avg,
    rolling 14-day avg, avg same weekday in last 4 weeks.
  - Model: LinearRegression per product + total covers.
  - Fallback: simple weighted moving average when data is insufficient.
  - Output: {date: {product: predicted_qty, ...}} for next 7 days.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, timedelta
from typing import Any


def _day_features(d: date) -> dict[str, float]:
    return {
        "day_of_week": d.weekday(),            # 0=Mon … 6=Sun
        "is_weekend": 1.0 if d.weekday() >= 5 else 0.0,
    }


def _rolling_avg(series: list[float], window: int) -> float:
    tail = series[-window:]
    return sum(tail) / len(tail) if tail else 0.0


def _same_weekday_avg(date_qty: list[tuple[date, float]], target_dow: int, n_weeks: int = 4) -> float:
    same = [qty for d, qty in date_qty if d.weekday() == target_dow][-n_weeks:]
    return sum(same) / len(same) if same else 0.0


def build_daily_totals(sales: list[dict[str, Any]]) -> dict[date, float]:
    """Sum quantities per day across all products."""
    totals: dict[date, float] = defaultdict(float)
    for row in sales:
        totals[row["date"]] += row["quantity"]
    return dict(sorted(totals.items()))


def build_product_series(sales: list[dict[str, Any]]) -> dict[str, dict[date, float]]:
    """Build per-product daily series."""
    series: dict[str, dict[date, float]] = defaultdict(lambda: defaultdict(float))
    for row in sales:
        series[row["product_name"]][row["date"]] += row["quantity"]
    return {k: dict(sorted(v.items())) for k, v in series.items()}


def _predict_series(date_qty: list[tuple[date, float]], future_dates: list[date]) -> dict[date, int]:
    """
    Predict future values for a single time series.
    Uses sklearn LinearRegression if scikit-learn is available,
    otherwise falls back to weighted moving average.
    """
    if len(date_qty) < 7:
        # Not enough data: use simple average
        avg = sum(q for _, q in date_qty) / len(date_qty) if date_qty else 0.0
        return {d: max(0, round(avg)) for d in future_dates}

    values = [q for _, q in date_qty]

    try:
        from sklearn.linear_model import LinearRegression
        import numpy as np

        X, y = [], []
        for i, (d, qty) in enumerate(date_qty):
            features = _day_features(d)
            r7 = _rolling_avg(values[:i], 7)
            r14 = _rolling_avg(values[:i], 14)
            sw4 = _same_weekday_avg(date_qty[:i], d.weekday(), 4)
            X.append([
                features["day_of_week"],
                features["is_weekend"],
                r7, r14, sw4,
            ])
            y.append(qty)

        model = LinearRegression()
        model.fit(np.array(X), np.array(y))

        preds = {}
        for d in future_dates:
            r7 = _rolling_avg(values, 7)
            r14 = _rolling_avg(values, 14)
            sw4 = _same_weekday_avg(date_qty, d.weekday(), 4)
            features = _day_features(d)
            x_pred = [[features["day_of_week"], features["is_weekend"], r7, r14, sw4]]
            pred = float(model.predict(np.array(x_pred))[0])
            preds[d] = max(0, round(pred))
        return preds

    except ImportError:
        # Fallback: weighted average (recent data weighted more)
        weights = [math.exp(i / len(values)) for i in range(len(values))]
        w_sum = sum(weights)
        w_avg = sum(v * w for v, w in zip(values, weights)) / w_sum
        preds = {}
        for d in future_dates:
            same_dow = _same_weekday_avg(date_qty, d.weekday(), 4)
            pred = (w_avg * 0.6 + same_dow * 0.4) if same_dow > 0 else w_avg
            preds[d] = max(0, round(pred))
        return preds


def generate_forecast(
    sales: list[dict[str, Any]],
    horizon_days: int = 7,
) -> list[dict[str, Any]]:
    """
    Generate a forecast for the next `horizon_days` days.

    Returns list of:
    {
        "date": date,
        "expected_covers": int,
        "product_predictions": {"product_name": predicted_qty, ...},
    }
    """
    if not sales:
        today = date.today()
        return [
            {
                "date": today + timedelta(days=i + 1),
                "expected_covers": 0,
                "product_predictions": {},
            }
            for i in range(horizon_days)
        ]

    future_dates = [date.today() + timedelta(days=i + 1) for i in range(horizon_days)]

    # Total covers forecast
    daily_totals = build_daily_totals(sales)
    covers_series = sorted(daily_totals.items())
    covers_preds = _predict_series(covers_series, future_dates)

    # Per-product forecast
    product_series = build_product_series(sales)
    product_preds: dict[str, dict[date, int]] = {}
    for product, date_qty_map in product_series.items():
        series = sorted(date_qty_map.items())
        product_preds[product] = _predict_series(series, future_dates)

    result = []
    for d in future_dates:
        pp = {prod: product_preds[prod].get(d, 0) for prod in product_preds}
        result.append({
            "date": d,
            "expected_covers": covers_preds.get(d, 0),
            "product_predictions": pp,
        })

    return result
