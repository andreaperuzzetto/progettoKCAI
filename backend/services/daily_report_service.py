import json
from datetime import date

from sqlalchemy.orm import Session

from backend.db.models import DailyReport
from backend.services.forecast_service import run_forecast
from backend.services.review_analysis_service import run_review_analysis
from backend.services.correlation_service import run_correlation


def generate_daily_report(restaurant_id, target_date: date, db: Session) -> dict:
    # 1. Forecast
    predictions = run_forecast(restaurant_id, target_date, db)

    # 2. Review analysis
    review_result = run_review_analysis(restaurant_id, db)

    # 3. Correlation
    correlation_result = run_correlation(restaurant_id, db)
    hypotheses = correlation_result.get("hypotheses", [])

    # Build report fields
    forecast_summary = "\n".join(
        f"{product}: {qty}" for product, qty in predictions.items()
    ) or "No forecast data available."

    issues = "\n".join(
        h["problem"] + ": " + h["possible_cause"]
        for h in hypotheses
    ) or "No issues detected."

    suggestions = "\n".join(
        h["suggested_action"]
        for h in hypotheses
    ) or "No suggestions at this time."

    # Store in DB
    report = DailyReport(
        restaurant_id=restaurant_id,
        date=target_date,
        forecast_summary=forecast_summary,
        issues=issues,
        suggestions=suggestions,
    )
    db.add(report)
    db.commit()

    return {
        "date": target_date.isoformat(),
        "forecast": predictions,
        "sentiments": review_result.get("sentiments", {}),
        "topics": review_result.get("topics", {}),
        "issues": issues,
        "suggestions": suggestions,
    }
