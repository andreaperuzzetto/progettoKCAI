"""Forecast service: generate, persist, and retrieve forecasts."""

import uuid
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from ai.forecasting_engine import generate_forecast
from backend.db.models import Forecast
from backend.services.sales_service import get_sales_history


def run_forecast(db: Session, restaurant_id: uuid.UUID, horizon_days: int = 7) -> list[dict[str, Any]]:
    """Generate forecast from historical sales and persist to DB."""
    sales = get_sales_history(db, restaurant_id, days=90)
    forecasts = generate_forecast(sales, horizon_days=horizon_days)

    # Upsert: delete existing forecasts for these dates, then insert fresh
    forecast_dates = [f["date"] for f in forecasts]
    db.query(Forecast).filter(
        Forecast.restaurant_id == restaurant_id,
        Forecast.date.in_(forecast_dates),
    ).delete(synchronize_session=False)

    saved = []
    for f in forecasts:
        row = Forecast(
            id=uuid.uuid4(),
            restaurant_id=restaurant_id,
            date=f["date"],
            expected_covers=f["expected_covers"],
            product_predictions=f["product_predictions"],
        )
        db.add(row)
        saved.append(row)
    db.commit()

    return [_serialize(r) for r in saved]


def get_latest_forecast(db: Session, restaurant_id: uuid.UUID) -> list[dict[str, Any]]:
    """Return the most recent forecast rows (next 7 days from today)."""
    today = date.today()
    rows = (
        db.query(Forecast)
        .filter(Forecast.restaurant_id == restaurant_id, Forecast.date >= today)
        .order_by(Forecast.date)
        .limit(7)
        .all()
    )
    return [_serialize(r) for r in rows]


def _serialize(f: Forecast) -> dict[str, Any]:
    return {
        "id": str(f.id),
        "date": str(f.date),
        "expected_covers": f.expected_covers,
        "product_predictions": f.product_predictions or {},
    }
