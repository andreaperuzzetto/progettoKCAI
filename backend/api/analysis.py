import uuid

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user, get_owned_restaurant
from backend.db.database import get_db
from backend.db.models import Restaurant, User
from backend.services.analysis_service import get_latest, run_analysis
from backend.services.usage_service import log_action

router = APIRouter(prefix="/analysis", tags=["analysis"])

ALLOWED_PERIODS = {"all", "last_30_days"}


def _check_subscription(user: User):
    if user.subscription_status not in ("active", "trial"):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required. Please upgrade at /billing.",
        )


@router.post("/run")
def run_analysis_endpoint(
    restaurant_id: uuid.UUID = Query(...),
    period: str = Query(default="all"),
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_subscription(current_user)
    if period not in ALLOWED_PERIODS:
        raise HTTPException(status_code=400, detail=f"period must be one of: {ALLOWED_PERIODS}")
    result = run_analysis(restaurant_id, period, db)
    log_action(current_user.id, "run_analysis", db)
    return {"status": "ok", **result}


@router.get("/latest")
def get_latest_analysis(
    restaurant_id: uuid.UUID = Query(...),
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    log_action(current_user.id, "view_dashboard", db)
    result = get_latest(restaurant_id, db)
    if result is None:
        return {"status": "ok", "analysis": None}
    return {"status": "ok", "analysis": result}
