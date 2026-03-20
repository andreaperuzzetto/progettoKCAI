"""Operations API: purchase orders and staff planning."""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user, get_owned_restaurant
from backend.db.database import get_db
from backend.db.models import Restaurant, User
from backend.services.plan_service import require_feature
from backend.services.operations_service import (
    generate_purchase_order, get_staff_plan, list_purchase_orders
)

router = APIRouter(prefix="/operations", tags=["operations"])


@router.post("/purchase-order")
def api_generate_purchase_order(
    for_date: Optional[date] = None,
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "forecast")
    return generate_purchase_order(db, restaurant.id, for_date)


@router.get("/purchase-orders")
def api_list_purchase_orders(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "forecast")
    return list_purchase_orders(db, restaurant.id)


@router.get("/staff-plan")
def api_staff_plan(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "forecast")
    return get_staff_plan(db, restaurant.id)
