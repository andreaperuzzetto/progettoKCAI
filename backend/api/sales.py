"""Sales upload and summary endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, timedelta
from collections import defaultdict

from backend.auth.dependencies import get_owned_restaurant
from backend.db.database import get_db
from backend.db.models import Restaurant, Sales
from backend.services.sales_service import parse_csv, store_sales

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("/upload")
async def upload_sales(
    file: UploadFile = File(...),
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: Session = Depends(get_db),
):
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")  # strip BOM if present
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    try:
        rows = parse_csv(text)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if not rows:
        raise HTTPException(status_code=422, detail="Nessuna riga valida trovata nel CSV")

    inserted = store_sales(db, restaurant.id, rows)
    return {"inserted": inserted, "total_rows": len(rows), "skipped": len(rows) - inserted}


@router.get("/summary")
def get_sales_summary(
    days: int = 30,
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: Session = Depends(get_db),
):
    """Aggregated sales summary: top products, daily totals."""
    cutoff = date.today() - timedelta(days=days)
    rows = (
        db.query(Sales)
        .filter(Sales.restaurant_id == restaurant.id, Sales.date >= cutoff)
        .order_by(Sales.date)
        .all()
    )

    product_totals: dict[str, int] = defaultdict(int)
    daily_totals: dict[str, int] = defaultdict(int)
    for r in rows:
        product_totals[r.product_name] += r.quantity
        daily_totals[str(r.date)] += r.quantity

    top_products = sorted(
        [{"name": k, "total_quantity": v} for k, v in product_totals.items()],
        key=lambda x: x["total_quantity"],
        reverse=True,
    )[:10]

    return {
        "period_days": days,
        "total_records": len(rows),
        "top_products": top_products,
        "daily_totals": [{"date": k, "total_quantity": v} for k, v in sorted(daily_totals.items())],
    }
