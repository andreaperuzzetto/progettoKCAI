import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_owned_restaurant
from backend.db.database import get_db
from backend.db.models import Restaurant
from backend.services.correlation_service import run_correlation

router = APIRouter()


@router.get("/correlation")
def get_correlation(
    restaurant_id: uuid.UUID = Query(...),
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: Session = Depends(get_db),
):
    result = run_correlation(restaurant_id, db)
    return {"status": "ok", **result}
