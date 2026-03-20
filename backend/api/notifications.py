"""Email notification endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models import User, Restaurant
from backend.services.email_service import send_daily_email
from backend.api.daily_report import get_daily_report as _build_report

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/send-daily")
async def send_daily(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually trigger the daily email for all user's restaurants."""
    restaurants = (
        db.query(Restaurant)
        .filter(Restaurant.owner_user_id == current_user.id)
        .all()
    )
    if not restaurants:
        raise HTTPException(status_code=404, detail="Nessun ristorante trovato")

    results = []
    for restaurant in restaurants:
        # Build report using a mock request context
        class _FakeReq:
            pass

        report_data = {
            "tomorrow": {"expected_covers": 0, "top_products": []},
            "suggestions": [],
            "review_summary": {},
        }
        try:
            from backend.services.forecast_service import get_latest_forecast
            from backend.services.sales_service import get_sales_history
            from backend.services.products_service import get_all_product_ingredient_mappings
            from backend.services.analysis_service import get_latest as get_latest_analysis
            from ai.suggestions_engine import generate_all_suggestions
            from ai.correlation_engine import run_correlation

            forecasts = get_latest_forecast(db, restaurant.id)
            tomorrow = forecasts[0] if forecasts else {"expected_covers": 0, "product_predictions": {}}
            historical = get_sales_history(db, restaurant.id, days=14)
            avg_covers = sum(r["quantity"] for r in historical) / 14.0 if historical else 0.0
            pim = get_all_product_ingredient_mappings(db, restaurant.id)
            op_suggestions = generate_all_suggestions(forecasts, pim, historical, avg_covers)
            analysis = get_latest_analysis(db, restaurant.id)
            issues = analysis.issues if analysis else []
            corr = run_correlation(issues, tomorrow)

            report_data = {
                "tomorrow": {
                    "expected_covers": tomorrow.get("expected_covers", 0),
                    "top_products": sorted(
                        [{"name": k, "predicted_qty": v} for k, v in (tomorrow.get("product_predictions") or {}).items() if v > 0],
                        key=lambda x: x["predicted_qty"], reverse=True
                    )[:5],
                },
                "suggestions": (corr + op_suggestions)[:5],
                "review_summary": {
                    "sentiment_positive": analysis.sentiment_positive if analysis else None,
                },
            }
        except Exception:
            pass

        sent = send_daily_email(current_user.email, restaurant.name, report_data)
        results.append({"restaurant": restaurant.name, "sent": sent})

    return {"results": results}
