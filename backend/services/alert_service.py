"""Alert service: detect conditions, persist, and retrieve alerts."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from ai.alert_engine import run_all_detections
from backend.db.models import Alert, AnalysisResult
from backend.services.forecast_service import get_latest_forecast
from backend.services.sales_service import get_sales_history


def generate_alerts(db: Session, restaurant_id: uuid.UUID) -> list[dict[str, Any]]:
    """Run all detectors and persist new alerts (avoid duplicates within 24h)."""
    # Gather context
    forecasts = get_latest_forecast(db, restaurant_id)
    historical = get_sales_history(db, restaurant_id, days=14)
    avg_covers = sum(r["quantity"] for r in historical) / 14.0 if historical else 0.0

    # Last two analyses
    analyses = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.restaurant_id == restaurant_id)
        .order_by(AnalysisResult.created_at.desc())
        .limit(2)
        .all()
    )
    analysis_now = analyses[0] if analyses else None
    analysis_prev = analyses[1] if len(analyses) > 1 else None

    detected = run_all_detections(
        forecast=forecasts,
        historical_sales=historical,
        avg_historical_covers=avg_covers,
        analysis_now=analysis_now,
        analysis_prev=analysis_prev,
    )

    # Deduplicate: skip if same type alert already exists in last 24h
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_types = {
        a.type
        for a in db.query(Alert)
        .filter(Alert.restaurant_id == restaurant_id, Alert.created_at >= cutoff)
        .all()
    }

    saved = []
    for d in detected:
        if d["type"] not in recent_types:
            alert = Alert(
                id=uuid.uuid4(),
                restaurant_id=restaurant_id,
                type=d["type"],
                severity=d.get("severity", "medium"),
                message=d["message"],
            )
            db.add(alert)
            saved.append(alert)
            recent_types.add(d["type"])  # prevent duplicates within same run

    db.commit()
    return [_serialize(a) for a in saved]


def get_alerts(db: Session, restaurant_id: uuid.UUID, unread_only: bool = False) -> list[dict[str, Any]]:
    q = db.query(Alert).filter(Alert.restaurant_id == restaurant_id)
    if unread_only:
        q = q.filter(Alert.read_at.is_(None))
    alerts = q.order_by(Alert.created_at.desc()).limit(50).all()
    return [_serialize(a) for a in alerts]


def mark_read(db: Session, alert_id: uuid.UUID, restaurant_id: uuid.UUID) -> dict[str, Any] | None:
    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id, Alert.restaurant_id == restaurant_id)
        .first()
    )
    if not alert:
        return None
    alert.read_at = datetime.utcnow()
    db.commit()
    return _serialize(alert)


def get_unread_count(db: Session, restaurant_id: uuid.UUID) -> int:
    return (
        db.query(Alert)
        .filter(Alert.restaurant_id == restaurant_id, Alert.read_at.is_(None))
        .count()
    )


def _serialize(a: Alert) -> dict[str, Any]:
    return {
        "id": str(a.id),
        "type": a.type,
        "severity": a.severity,
        "message": a.message,
        "created_at": a.created_at.isoformat(),
        "read": a.read_at is not None,
    }
