"""Forecast endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_owned_restaurant
from backend.db.database import get_db
from backend.db.models import Restaurant
from backend.services.forecast_service import run_forecast, get_latest_forecast

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.post("/generate")
def generate(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: Session = Depends(get_db),
):
    forecasts = run_forecast(db, restaurant.id)
    return {"generated": len(forecasts), "forecasts": forecasts}


@router.get("/latest")
def latest(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: Session = Depends(get_db),
):
    forecasts = get_latest_forecast(db, restaurant.id)
    if not forecasts:
        return {"forecasts": [], "message": "Nessuna previsione disponibile. Esegui /forecast/generate prima."}
    return {"forecasts": forecasts}
