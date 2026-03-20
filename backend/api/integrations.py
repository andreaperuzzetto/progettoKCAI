"""Integrations API."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import uuid
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user, get_owned_restaurant
from backend.db.database import get_db
from backend.db.models import Restaurant, User
from backend.services.plan_service import require_feature
from backend.services.integration_service import (
    create_integration, list_integrations, sync_integration, ProviderError
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


class IntegrationCreate(BaseModel):
    provider: str
    config: dict[str, Any] = {}


@router.post("")
def api_create_integration(
    body: IntegrationCreate,
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "integrations")
    try:
        result = create_integration(db, restaurant.id, body.provider, body.config)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("")
def api_list_integrations(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "integrations")
    return list_integrations(db, restaurant.id)


@router.post("/{integration_id}/sync")
def api_sync_integration(
    integration_id: uuid.UUID,
    restaurant: Restaurant = Depends(get_owned_restaurant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature(current_user, "integrations")
    try:
        return sync_integration(db, integration_id, restaurant.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))
