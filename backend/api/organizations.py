"""Organizations API — multi-location management."""
import uuid
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models import User
from backend.services.organization_service import (
    create_organization, get_user_organization,
    add_restaurant_to_org, compare_locations, get_market_benchmark
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


class OrgCreate(BaseModel):
    name: str


@router.post("")
def api_create_org(
    body: OrgCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_organization(db, current_user, body.name)


@router.get("/me")
def api_my_org(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org = get_user_organization(db, current_user)
    if not org:
        raise HTTPException(status_code=404, detail="Nessuna organizzazione trovata. Creane una prima.")
    return org


@router.post("/restaurants/{restaurant_id}")
def api_add_restaurant(
    restaurant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return add_restaurant_to_org(db, current_user, restaurant_id)


@router.get("/compare")
def api_compare(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="Nessuna organizzazione attiva.")
    return compare_locations(db, current_user.organization_id)


@router.get("/benchmark")
def api_benchmark(
    restaurant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_market_benchmark(db, restaurant_id)
