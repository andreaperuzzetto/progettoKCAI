"""
Daily report endpoint — aggregates forecast + suggestions + review issues.
This is the single endpoint the dashboard calls every morning.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from backend.auth.dependencies import get_owned_restaurant
from backend.db.database import get_db
from backend.db.models import Restaurant
from backend.services.forecast_service import get_latest_forecast
from backend.services.sales_service import get_sales_history
from backend.services.products_service import get_all_product_ingredient_mappings
from backend.services.analysis_service import get_latest as get_latest_analysis
from ai.suggestions_engine import generate_all_suggestions
from ai.correlation_engine import run_correlation

router = APIRouter(prefix="/daily-report", tags=["daily-report"])


@router.get("")
def get_daily_report(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: Session = Depends(get_db),
):
    """
    Returns a combined daily report:
      - tomorrow's forecast (covers + top products)
      - operational suggestions (inventory, staffing, menu)
      - correlation suggestions (reviews issues × forecast)
      - latest review analysis summary
    """
    rid = restaurant.id

    # 1. Forecast
    forecasts = get_latest_forecast(db, rid)
    tomorrow_forecast = forecasts[0] if forecasts else {"expected_covers": 0, "product_predictions": {}}

    # 2. Historical sales (for suggestions engine)
    historical = get_sales_history(db, rid, days=14)
    avg_covers = (
        sum(r["quantity"] for r in historical) / 14.0
        if historical else 0.0
    )

    # 3. Product → ingredient map
    product_ingredient_map = get_all_product_ingredient_mappings(db, rid)

    # 4. Operational suggestions
    op_suggestions = generate_all_suggestions(
        forecast=forecasts,
        product_ingredient_map=product_ingredient_map,
        historical_sales=historical,
        avg_historical_covers=avg_covers,
    )

    # 5. Review issues + correlation
    analysis = get_latest_analysis(rid, db)
    issues = analysis.issues if analysis else []
    correlation_suggestions = run_correlation(issues, tomorrow_forecast)

    # 6. Merge all suggestions, deduplicate by message
    all_suggestions = correlation_suggestions + op_suggestions
    seen: set[str] = set()
    unique_suggestions = []
    for s in all_suggestions:
        if s["message"] not in seen:
            seen.add(s["message"])
            unique_suggestions.append(s)

    # 7. Top products for tomorrow (sorted by predicted qty)
    top_products_tomorrow = sorted(
        [
            {"name": k, "predicted_qty": v}
            for k, v in (tomorrow_forecast.get("product_predictions") or {}).items()
            if v > 0
        ],
        key=lambda x: x["predicted_qty"],
        reverse=True,
    )[:5]

    return {
        "date": str(date.today()),
        "restaurant_id": str(rid),
        "tomorrow": {
            "date": tomorrow_forecast.get("date"),
            "expected_covers": tomorrow_forecast.get("expected_covers", 0),
            "top_products": top_products_tomorrow,
        },
        "forecast_7days": forecasts,
        "suggestions": unique_suggestions[:10],
        "review_summary": {
            "sentiment_positive": analysis.sentiment_positive if analysis else None,
            "sentiment_negative": analysis.sentiment_negative if analysis else None,
            "top_issues": issues[:3] if issues else [],
        },
    }
