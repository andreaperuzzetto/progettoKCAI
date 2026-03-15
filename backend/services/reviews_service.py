import csv
import io
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.db.models import Reviews


REQUIRED_FIELDS = {"date", "platform", "review_text"}


def _validate_row(row: dict, index: int) -> dict:
    if not row.get("date"):
        raise HTTPException(status_code=400, detail=f"Row {index}: missing date.")

    try:
        parsed_date = date.fromisoformat(row["date"])
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Row {index}: invalid date '{row['date']}'. Expected YYYY-MM-DD.",
        )

    if not row.get("platform"):
        raise HTTPException(status_code=400, detail=f"Row {index}: missing platform.")

    if not row.get("review_text"):
        raise HTTPException(status_code=400, detail=f"Row {index}: missing review_text.")

    return {"date": parsed_date, "platform": row["platform"], "review_text": row["review_text"]}


def parse_csv(content: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(content))

    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file is empty.")

    # Accept "review" as alias for "review_text" (matches example CSV)
    columns = set(reader.fieldnames)
    if "review" in columns and "review_text" not in columns:
        columns = (columns - {"review"}) | {"review_text"}
        alias = True
    else:
        alias = False

    missing = REQUIRED_FIELDS - columns
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(sorted(missing))}",
        )

    rows = []
    for i, row in enumerate(reader, start=2):
        if alias:
            row["review_text"] = row.pop("review", "")
        rows.append(_validate_row(row, i))

    if not rows:
        raise HTTPException(status_code=400, detail="CSV file contains no data rows.")

    return rows


def validate_json_reviews(items: list[dict]) -> list[dict]:
    if not items:
        raise HTTPException(status_code=400, detail="JSON payload is empty.")

    rows = []
    for i, item in enumerate(items, start=1):
        rows.append(_validate_row(item, i))
    return rows


def store_reviews(rows: list[dict], restaurant_id, db: Session) -> int:
    records = [
        Reviews(
            restaurant_id=restaurant_id,
            date=r["date"],
            platform=r["platform"],
            review_text=r["review_text"],
            sentiment=None,
        )
        for r in rows
    ]
    db.add_all(records)
    db.commit()
    return len(records)
