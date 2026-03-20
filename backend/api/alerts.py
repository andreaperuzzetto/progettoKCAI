"""Alerts API."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user, get_owned_restaurant
from backend.db.database import get_db
from backend.db.models import Restaurant, User
from backend.services.plan_service import require_feature
from backend.services.alert_service import generate_alerts, get_alerts, mark_read, get_unread_count

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/generate")
def api_generate_alerts(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "alerts")
    new_alerts = generate_alerts(db, restaurant.id)
    return {"generated": len(new_alerts), "alerts": new_alerts}


@router.get("")
def api_get_alerts(
    unread_only: bool = False,
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "alerts")
    alerts = get_alerts(db, restaurant.id, unread_only=unread_only)
    unread = get_unread_count(db, restaurant.id)
    return {"alerts": alerts, "unread_count": unread}


@router.post("/{alert_id}/read")
def api_mark_read(
    alert_id: uuid.UUID,
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: Session = Depends(get_db),
):
    result = mark_read(db, alert_id, restaurant.id)
    if not result:
        raise HTTPException(status_code=404, detail="Alert non trovato")
    return result
