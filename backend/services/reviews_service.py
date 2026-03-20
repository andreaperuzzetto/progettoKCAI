import csv
import io
import uuid
from datetime import date

from sqlalchemy.orm import Session

from backend.db.models import Reviews


def _parse_date(val: str) -> date | None:
    if not val:
        return None
    try:
        return date.fromisoformat(val.strip())
    except ValueError:
        return None


def parse_csv(content: str) -> list[dict]:
    """Parse reviews CSV. Accepts columns: review_text or review, date (optional), platform (optional), rating (optional)."""
    reader = csv.DictReader(io.StringIO(content))
    rows = []
    for row in reader:
        text = row.get("review_text") or row.get("review") or row.get("text") or ""
        text = text.strip()
        if not text:
            continue
        rows.append({
            "review_text": text,
            "date": _parse_date(row.get("date", "")),
            "platform": (row.get("platform") or "").strip() or None,
            "rating": _parse_rating(row.get("rating")),
        })
    return rows


def parse_text_list(texts: list[str]) -> list[dict]:
    """Convert a list of raw review strings to review dicts."""
    result = []
    for text in texts:
        text = text.strip()
        if len(text) < 5:
            continue
        result.append({"review_text": text, "date": None, "platform": None, "rating": None})
    return result


def _parse_rating(val) -> int | None:
    if val is None:
        return None
    try:
        r = int(str(val).strip())
        return r if 1 <= r <= 5 else None
    except (ValueError, TypeError):
        return None


def store_reviews(rows: list[dict], restaurant_id: uuid.UUID, db: Session) -> int:
    """Batch insert reviews, skipping exact text duplicates already in DB."""
    existing_texts = {
        r.review_text
        for r in db.query(Reviews.review_text).filter(Reviews.restaurant_id == restaurant_id).all()
    }
    new_rows = [r for r in rows if r["review_text"] not in existing_texts]
    for row in new_rows:
        db.add(Reviews(
            restaurant_id=restaurant_id,
            review_text=row["review_text"],
            date=row.get("date"),
            platform=row.get("platform"),
            rating=row.get("rating"),
        ))
    db.commit()
    return len(new_rows)
