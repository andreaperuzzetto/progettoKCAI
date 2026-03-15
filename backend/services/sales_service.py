import csv
import io
from datetime import date

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from backend.db.models import Sales


REQUIRED_COLUMNS = {"date", "product", "quantity"}


def parse_and_validate_csv(content: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(content))

    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file is empty.")

    missing = REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(sorted(missing))}",
        )

    rows = []
    for i, row in enumerate(reader, start=2):
        if not row.get("date"):
            raise HTTPException(status_code=400, detail=f"Row {i}: missing date.")

        try:
            parsed_date = date.fromisoformat(row["date"])
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Row {i}: invalid date '{row['date']}'. Expected YYYY-MM-DD.",
            )

        if not row.get("product"):
            raise HTTPException(status_code=400, detail=f"Row {i}: missing product.")

        try:
            quantity = int(row["quantity"])
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400,
                detail=f"Row {i}: invalid quantity '{row['quantity']}'. Must be an integer.",
            )

        if quantity < 0:
            raise HTTPException(
                status_code=400, detail=f"Row {i}: quantity must not be negative."
            )

        rows.append({"date": parsed_date, "product": row["product"], "quantity": quantity})

    if not rows:
        raise HTTPException(status_code=400, detail="CSV file contains no data rows.")

    return rows


async def upload_sales(file: UploadFile, restaurant_id, db: Session) -> int:
    raw = await file.read()
    content = raw.decode("utf-8")
    rows = parse_and_validate_csv(content)

    records = [
        Sales(restaurant_id=restaurant_id, date=r["date"], product=r["product"], quantity=r["quantity"])
        for r in rows
    ]
    db.add_all(records)
    db.commit()

    return len(records)
