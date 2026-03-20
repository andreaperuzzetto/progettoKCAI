import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_owned_restaurant
from backend.db.database import get_db
from backend.db.models import Restaurant
from backend.services.daily_report_service import generate_daily_report

router = APIRouter()


@router.get("/daily-report")
def get_daily_report(
    restaurant_id: uuid.UUID = Query(...),
    target_date: date = Query(default_factory=date.today),
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: Session = Depends(get_db),
):
    result = generate_daily_report(restaurant_id, target_date, db)
    return {"status": "ok", **result}
