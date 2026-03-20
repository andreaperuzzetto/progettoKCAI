"""Forecast endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user, get_owned_restaurant
from backend.db.database import get_db
from backend.db.models import Restaurant, User
from backend.services.forecast_service import run_forecast, get_latest_forecast
from backend.services.plan_service import require_feature

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.post("/generate")
def generate(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "forecast")
    forecasts = run_forecast(db, restaurant.id)
    return {"generated": len(forecasts), "forecasts": forecasts}


@router.get("/latest")
def latest(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "forecast")
    forecasts = get_latest_forecast(db, restaurant.id)
    if not forecasts:
        return {"forecasts": [], "message": "Nessuna previsione disponibile. Esegui /forecast/generate prima."}
    return {"forecasts": forecasts}
