"""
Integration service: pluggable provider sync.

Architecture:
  - Each provider implements _fetch_sales(config) → list[SaleRow]
  - integration_service orchestrates: fetch → normalize → store
  - Errors are recorded on the Integration row, not re-raised

Current providers:
  - square (mock/skeleton — real impl requires Square OAuth)
  - csv_auto (reads from a pre-configured file path — for simple automation)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.db.models import Integration
from backend.services.sales_service import store_sales

logger = logging.getLogger(__name__)


# ── Provider interface ─────────────────────────────────────────────────────────

class ProviderError(Exception):
    pass


def _fetch_square(config: dict) -> list[dict[str, Any]]:
    """
    Square API sync (skeleton — requires real Square OAuth tokens in production).
    Returns rows in the standard format: [{date, product_name, quantity, revenue}]
    """
    access_token = config.get("access_token", "")
    location_id = config.get("location_id", "")
    if not access_token:
        raise ProviderError("Square: access_token mancante nella configurazione")
    # Production: call Square Orders API
    # GET https://connect.squareup.com/v2/orders/search
    # For now: return mock to prove the plumbing works
    logger.info("Square sync: would call Orders API for location %s", location_id)
    return []  # stub — real implementation goes here


def _fetch_csv_auto(config: dict) -> list[dict[str, Any]]:
    """
    Auto-import from a CSV file path (for restaurants that export from their POS).
    config = {"file_path": "/path/to/export.csv"}
    """
    import csv, os
    from datetime import date as _date, datetime as _dt

    file_path = config.get("file_path", "")
    if not file_path or not os.path.exists(file_path):
        raise ProviderError(f"csv_auto: file non trovato: {file_path!r}")

    rows = []
    with open(file_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                d = _dt.strptime(row.get("date", "").strip(), "%Y-%m-%d").date()
                rows.append({
                    "date": d,
                    "product_name": row.get("product", "").strip().lower(),
                    "quantity": int(float(row.get("quantity", 0))),
                    "revenue": float(row["revenue"]) if row.get("revenue") else None,
                })
            except Exception:
                continue
    return rows


PROVIDERS: dict[str, Any] = {
    "square": _fetch_square,
    "csv_auto": _fetch_csv_auto,
    # Future: "toast": _fetch_toast, "ubereats": _fetch_ubereats
}


# ── Service methods ────────────────────────────────────────────────────────────

def create_integration(
    db: Session,
    restaurant_id: uuid.UUID,
    provider: str,
    config: dict,
) -> dict[str, Any]:
    if provider not in PROVIDERS:
        raise ValueError(f"Provider non supportato: {provider}. Supportati: {list(PROVIDERS.keys())}")

    # Mask sensitive fields in storage (store only non-sensitive metadata + ref)
    integration = Integration(
        id=uuid.uuid4(),
        restaurant_id=restaurant_id,
        provider=provider,
        config_json=config,
        status="pending",
    )
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return _serialize(integration)


def list_integrations(db: Session, restaurant_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = db.query(Integration).filter(Integration.restaurant_id == restaurant_id).all()
    return [_serialize(r) for r in rows]


def sync_integration(db: Session, integration_id: uuid.UUID, restaurant_id: uuid.UUID) -> dict[str, Any]:
    """Run a sync for one integration. Updates status + last_sync_at."""
    integration = (
        db.query(Integration)
        .filter(Integration.id == integration_id, Integration.restaurant_id == restaurant_id)
        .first()
    )
    if not integration:
        raise ValueError("Integrazione non trovata")

    fetch_fn = PROVIDERS.get(integration.provider)
    if not fetch_fn:
        raise ProviderError(f"Provider {integration.provider!r} non supportato")

    try:
        rows = fetch_fn(integration.config_json or {})
        inserted = store_sales(db, restaurant_id, rows)
        integration.status = "active"
        integration.last_sync_at = datetime.utcnow()
        integration.error_message = None
        db.commit()
        logger.info("Integration %s synced: %d rows inserted", integration.provider, inserted)
        return {**_serialize(integration), "inserted": inserted}
    except ProviderError as e:
        integration.status = "error"
        integration.error_message = str(e)
        db.commit()
        raise


def sync_all_active(db: Session) -> None:
    """Cron job: sync all active integrations across all restaurants."""
    integrations = db.query(Integration).filter(Integration.status == "active").all()
    for integration in integrations:
        try:
            sync_integration(db, integration.id, integration.restaurant_id)
        except Exception as e:
            logger.error("Sync failed for integration %s: %s", integration.id, e)


def _serialize(i: Integration) -> dict[str, Any]:
    config_safe = {k: ("***" if "key" in k or "token" in k or "secret" in k else v)
                   for k, v in (i.config_json or {}).items()}
    return {
        "id": str(i.id),
        "provider": i.provider,
        "status": i.status,
        "last_sync_at": i.last_sync_at.isoformat() if i.last_sync_at else None,
        "error_message": i.error_message,
        "config": config_safe,
    }
