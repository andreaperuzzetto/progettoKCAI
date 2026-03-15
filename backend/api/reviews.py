import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.services.reviews_service import parse_csv, validate_json_reviews, store_reviews

router = APIRouter()


@router.post("/upload-reviews")
async def upload_reviews_csv(
    file: UploadFile = File(...),
    restaurant_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
):
    raw = await file.read()
    content = raw.decode("utf-8")
    rows = parse_csv(content)
    count = store_reviews(rows, restaurant_id, db)
    return {"status": "ok", "rows_imported": count}


@router.post("/upload-reviews-json")
def upload_reviews_json(
    reviews: list[dict],
    restaurant_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
):
    rows = validate_json_reviews(reviews)
    count = store_reviews(rows, restaurant_id, db)
    return {"status": "ok", "rows_imported": count}
