import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user, get_owned_restaurant
from backend.db.database import get_db
from backend.db.models import Restaurant, User
from backend.services.reviews_service import parse_csv, parse_text_list, store_reviews
from backend.services.usage_service import log_action

router = APIRouter(prefix="/reviews", tags=["reviews"])


class TextReviewsRequest(BaseModel):
    reviews: list[str]


@router.post("/upload")
async def upload_reviews(
    restaurant_id: uuid.UUID = Query(...),
    file: Optional[UploadFile] = File(None),
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload reviews via CSV file. The restaurant_id query param is required."""
    if file is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide a CSV file")
    raw = await file.read()
    content = raw.decode("utf-8")
    rows = parse_csv(content)
    count = store_reviews(rows, restaurant_id, db)
    log_action(current_user.id, "upload_reviews", db)
    return {"status": "ok", "rows_imported": count}


@router.post("/upload-text")
def upload_reviews_text(
    payload: TextReviewsRequest,
    restaurant_id: uuid.UUID = Query(...),
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload reviews as a JSON list of strings (free text)."""
    rows = parse_text_list(payload.reviews)
    count = store_reviews(rows, restaurant_id, db)
    log_action(current_user.id, "upload_reviews", db)
    return {"status": "ok", "rows_imported": count}
