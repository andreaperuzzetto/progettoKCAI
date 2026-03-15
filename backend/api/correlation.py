import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.services.correlation_service import run_correlation

router = APIRouter()


@router.get("/correlation")
def get_correlation(
    restaurant_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
):
    result = run_correlation(restaurant_id, db)
    return {"status": "ok", **result}
