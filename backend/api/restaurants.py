import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models import Restaurant, User

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


class RestaurantOut(BaseModel):
    id: uuid.UUID
    name: str
    city: Optional[str] = None
    category: Optional[str] = None

    model_config = {"from_attributes": True}


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    category: Optional[str] = None


@router.get("", response_model=list[RestaurantOut])
def list_restaurants(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Restaurant).filter(Restaurant.owner_user_id == current_user.id).all()


@router.get("/{restaurant_id}", response_model=RestaurantOut)
def get_restaurant(
    restaurant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id,
        Restaurant.owner_user_id == current_user.id,
    ).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return r


@router.patch("/{restaurant_id}", response_model=RestaurantOut)
def update_restaurant(
    restaurant_id: uuid.UUID,
    body: RestaurantUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id,
        Restaurant.owner_user_id == current_user.id,
    ).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    if body.name is not None:
        r.name = body.name
    if body.city is not None:
        r.city = body.city
    if body.category is not None:
        r.category = body.category
    db.commit()
    db.refresh(r)
    return r

