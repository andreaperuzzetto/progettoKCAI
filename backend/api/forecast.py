import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.services.forecast_service import run_forecast

router = APIRouter()


@router.get("/forecast")
def get_forecast(
    restaurant_id: uuid.UUID = Query(...),
    target_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
):
    predictions = run_forecast(restaurant_id, target_date, db)
    return {
        "status": "ok",
        "target_date": target_date.isoformat(),
        "predictions": predictions,
    }
