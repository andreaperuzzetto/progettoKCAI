"""Correlations API (LLM-based)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user, get_owned_restaurant
from backend.db.database import get_db
from backend.db.models import Restaurant, User
from backend.services.plan_service import require_feature
from backend.services.correlation_service import run_correlation, get_latest_correlation

router = APIRouter(prefix="/correlations", tags=["correlations"])


@router.post("/run")
def api_run_correlation(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "correlations_v2")
    results = run_correlation(db, restaurant.id)
    return {"correlations": results, "count": len(results)}


@router.get("/latest")
def api_latest_correlation(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "correlations_v2")
    results = get_latest_correlation(db, restaurant.id)
    return {"correlations": results}
