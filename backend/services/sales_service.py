"""Sales ingestion: CSV parsing, normalization, dedup, batch insert."""

import csv
import io
import re
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.db.models import Sales


def _normalize_product_name(name: str) -> str:
    """Lowercase, strip, collapse whitespace."""
    return re.sub(r"\s+", " ", name.strip().lower())


def parse_csv(content: str) -> list[dict[str, Any]]:
    """
    Parse CSV with columns: date, product, quantity [, revenue].
    Returns list of cleaned row dicts.
    """
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        raise ValueError("CSV vuoto o senza intestazione")

    # Accept flexible column names
    fieldnames_lower = {f.strip().lower(): f for f in reader.fieldnames}
    date_col = _find_col(fieldnames_lower, ["date", "data"])
    product_col = _find_col(fieldnames_lower, ["product", "prodotto", "item", "piatto"])
    quantity_col = _find_col(fieldnames_lower, ["quantity", "qty", "quantita", "quantità", "pezzi"])
    revenue_col = _find_col(fieldnames_lower, ["revenue", "ricavo", "importo", "totale"], required=False)

    rows: list[dict[str, Any]] = []
    for i, row in enumerate(reader, start=2):
        try:
            sale_date = _parse_date(row[date_col].strip())
            product = _normalize_product_name(row[product_col])
            quantity = int(float(row[quantity_col].strip()))
            revenue = None
            if revenue_col and row.get(revenue_col, "").strip():
                revenue = float(row[revenue_col].strip().replace(",", "."))
            if quantity <= 0:
                continue
            rows.append({"date": sale_date, "product_name": product, "quantity": quantity, "revenue": revenue})
        except Exception as e:
            raise ValueError(f"Riga {i}: {e}")
    return rows


def _find_col(fieldnames_lower: dict[str, str], candidates: list[str], required: bool = True) -> str:
    for c in candidates:
        if c in fieldnames_lower:
            return fieldnames_lower[c]
    if required:
        raise ValueError(f"Colonna mancante. Attese: {candidates}")
    return ""


def _parse_date(val: str) -> date:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Formato data non riconosciuto: {val!r}")


def store_sales(db: Session, restaurant_id: uuid.UUID, rows: list[dict[str, Any]]) -> int:
    """Insert rows, skip exact duplicates (same date+product+quantity)."""
    inserted = 0
    for row in rows:
        exists = (
            db.query(Sales)
            .filter(
                Sales.restaurant_id == restaurant_id,
                Sales.date == row["date"],
                Sales.product_name == row["product_name"],
                Sales.quantity == row["quantity"],
            )
            .first()
        )
        if not exists:
            db.add(Sales(id=uuid.uuid4(), restaurant_id=restaurant_id, **row))
            inserted += 1
    db.commit()
    return inserted


def get_sales_history(db: Session, restaurant_id: uuid.UUID, days: int = 60) -> list[dict[str, Any]]:
    """Return sales rows for the last N days, ordered by date."""
    from datetime import timedelta
    cutoff = date.today() - timedelta(days=days)
    rows = (
        db.query(Sales)
        .filter(Sales.restaurant_id == restaurant_id, Sales.date >= cutoff)
        .order_by(Sales.date)
        .all()
    )
    return [
        {"date": r.date, "product_name": r.product_name, "quantity": r.quantity, "revenue": r.revenue}
        for r in rows
    ]
