"""Menu optimization API."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user, get_owned_restaurant
from backend.db.database import get_db
from backend.db.models import Restaurant, User
from backend.services.plan_service import require_feature
from backend.services.menu_service import get_menu_suggestions, compute_product_metrics

router = APIRouter(prefix="/menu", tags=["menu"])


@router.post("/analyze")
def api_analyze_menu(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "forecast")  # pro+
    return get_menu_suggestions(db, restaurant.id)


@router.get("/metrics")
def api_product_metrics(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "forecast")
    metrics = compute_product_metrics(db, restaurant.id)
    return {"metrics": metrics, "count": len(metrics)}
