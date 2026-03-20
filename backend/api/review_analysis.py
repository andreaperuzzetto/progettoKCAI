import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_owned_restaurant
from backend.db.database import get_db
from backend.db.models import Restaurant
from backend.services.review_analysis_service import run_review_analysis

router = APIRouter()


@router.get("/review-analysis")
def get_review_analysis(
    restaurant_id: uuid.UUID = Query(...),
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: Session = Depends(get_db),
):
    result = run_review_analysis(restaurant_id, db)
    return {"status": "ok", **result}
