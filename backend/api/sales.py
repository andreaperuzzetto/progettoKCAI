import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.services.sales_service import upload_sales

router = APIRouter()


@router.post("/upload-sales")
async def upload_sales_endpoint(
    file: UploadFile = File(...),
    restaurant_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
):
    count = await upload_sales(file, restaurant_id, db)
    return {"status": "ok", "rows_imported": count}
