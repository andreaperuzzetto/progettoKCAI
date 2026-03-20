"""Correlation service: run LLM analysis and persist results."""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from ai.correlation_engine_v2 import run_llm_correlation
from backend.config import settings
from backend.db.models import CorrelationResult
from backend.services.forecast_service import get_latest_forecast
from backend.services.sales_service import get_sales_history


def run_correlation(db: Session, restaurant_id: uuid.UUID) -> list[dict[str, Any]]:
    forecasts = get_latest_forecast(db, restaurant_id)
    tomorrow = forecasts[0] if forecasts else {"expected_covers": 0, "product_predictions": {}}
    historical = get_sales_history(db, restaurant_id, days=14)
    avg_covers = sum(r["quantity"] for r in historical) / 14.0 if historical else 0.0

    from backend.db.models import AnalysisResult
    analysis = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.restaurant_id == restaurant_id)
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )
    issues = analysis.issues if analysis else []

    correlations = run_llm_correlation(
        sales=historical,
        forecast_tomorrow=tomorrow,
        issues=issues,
        avg_covers=avg_covers,
        api_key=settings.openai_api_key,
    )

    result = CorrelationResult(
        id=uuid.uuid4(),
        restaurant_id=restaurant_id,
        correlations=correlations,
    )
    db.add(result)
    db.commit()
    return correlations


def get_latest_correlation(db: Session, restaurant_id: uuid.UUID) -> list[dict[str, Any]]:
    row = (
        db.query(CorrelationResult)
        .filter(CorrelationResult.restaurant_id == restaurant_id)
        .order_by(CorrelationResult.created_at.desc())
        .first()
    )
    return row.correlations if row else []
