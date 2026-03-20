import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models import Restaurant, User

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


class RestaurantOut(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


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
    from fastapi import HTTPException, status
    r = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id,
        Restaurant.owner_user_id == current_user.id,
    ).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return r
