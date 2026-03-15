import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.services.review_analysis_service import run_review_analysis

router = APIRouter()


@router.get("/review-analysis")
def get_review_analysis(
    restaurant_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
):
    result = run_review_analysis(restaurant_id, db)
    return {"status": "ok", **result}
