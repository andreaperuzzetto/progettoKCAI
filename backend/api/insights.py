"""Insights API — proactive AI insights."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user, get_owned_restaurant
from backend.db.database import get_db
from backend.db.models import Restaurant, User
from backend.services.plan_service import require_feature
from backend.services.insights_service import generate_insights, get_latest_insights, mark_insight_read

router = APIRouter(prefix="/insights", tags=["insights"])


@router.post("/generate")
def api_generate_insights(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "alerts")  # pro+
    results = generate_insights(db, restaurant.id)
    return {"insights": results, "count": len(results)}


@router.get("/latest")
def api_latest_insights(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "alerts")
    return {"insights": get_latest_insights(db, restaurant.id)}


@router.post("/{insight_id}/read")
def api_mark_read(
    insight_id: uuid.UUID,
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: Session = Depends(get_db),
):
    result = mark_insight_read(db, insight_id, restaurant.id)
    if not result:
        raise HTTPException(status_code=404, detail="Insight non trovato")
    return result
