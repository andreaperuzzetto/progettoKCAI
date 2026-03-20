"""Insights service: generate and retrieve AI insights."""
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.models import Insight, Sales, Forecast, AnalysisResult, Restaurant
from backend.config import settings
from ai.insights_engine import run_insights


def _get_sales_window(db: Session, restaurant_id: uuid.UUID, days: int, offset: int = 0):
    from datetime import date, timedelta
    from sqlalchemy import func
    today = date.today()
    end = today - timedelta(days=offset)
    start = end - timedelta(days=days)
    rows = db.query(Sales).filter(
        Sales.restaurant_id == restaurant_id,
        Sales.date >= start,
        Sales.date <= end,
    ).all()
    return [{"date": str(r.date), "product_name": r.product_name, "quantity": r.quantity} for r in rows]


def generate_insights(db: Session, restaurant_id: uuid.UUID) -> list[dict]:
    """Run insights engine and persist top 3."""
    sales_last7 = _get_sales_window(db, restaurant_id, 7)
    sales_prev7 = _get_sales_window(db, restaurant_id, 7, offset=7)

    # Latest forecast for tomorrow
    from datetime import date, timedelta
    tomorrow = date.today() + timedelta(days=1)
    fc = db.query(Forecast).filter(
        Forecast.restaurant_id == restaurant_id,
        Forecast.date == tomorrow,
    ).first()
    forecast_tomorrow = {"expected_covers": fc.expected_covers, "product_predictions": fc.product_predictions} if fc else None

    # Avg covers (last 30 days)
    all_fc = db.query(Forecast).filter(Forecast.restaurant_id == restaurant_id).all()
    avg_covers = sum(f.expected_covers for f in all_fc) / len(all_fc) if all_fc else 30

    # Issues from latest analysis
    latest = db.query(AnalysisResult).filter(
        AnalysisResult.restaurant_id == restaurant_id,
    ).order_by(AnalysisResult.created_at.desc()).first()
    issues = latest.issues if latest else []

    results = run_insights(
        sales_last7=sales_last7,
        sales_prev7=sales_prev7,
        forecast_tomorrow=forecast_tomorrow,
        issues=issues,
        avg_covers=avg_covers,
        api_key=settings.openai_api_key or "",
    )

    # Persist (clear old unread first to avoid clutter)
    db.query(Insight).filter(
        Insight.restaurant_id == restaurant_id,
        Insight.read_at.is_(None),
    ).delete()

    saved = []
    for r in results:
        ins = Insight(
            restaurant_id=restaurant_id,
            type=r.get("type", "prescriptive"),
            message=r["message"],
            confidence=float(r.get("confidence", 0.5)),
            impact=float(r.get("impact", 0.5)),
        )
        db.add(ins)
        saved.append(ins)
    db.commit()

    return [
        {"id": str(i.id), "type": i.type, "message": i.message,
         "confidence": i.confidence, "impact": i.impact, "created_at": str(i.created_at)}
        for i in saved
    ]


def get_latest_insights(db: Session, restaurant_id: uuid.UUID) -> list[dict]:
    rows = db.query(Insight).filter(
        Insight.restaurant_id == restaurant_id,
    ).order_by(Insight.created_at.desc()).limit(10).all()
    return [
        {"id": str(i.id), "type": i.type, "message": i.message,
         "confidence": i.confidence, "impact": i.impact,
         "read": i.read_at is not None, "created_at": str(i.created_at)}
        for i in rows
    ]


def mark_insight_read(db: Session, insight_id: uuid.UUID, restaurant_id: uuid.UUID) -> dict | None:
    ins = db.query(Insight).filter(
        Insight.id == insight_id,
        Insight.restaurant_id == restaurant_id,
    ).first()
    if not ins:
        return None
    ins.read_at = datetime.utcnow()
    db.commit()
    return {"id": str(ins.id), "read": True}
