import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.auth.utils import create_access_token, hash_password, verify_password
from backend.db.database import get_db
from backend.db.models import Restaurant, User

router = APIRouter(prefix="/auth", tags=["auth"])


# --- Schemas ---

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RestaurantCreateRequest(BaseModel):
    name: str


class RestaurantOut(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    user_id: uuid.UUID
    email: str
    restaurants: list[RestaurantOut]


# --- Routes ---

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    restaurants = db.query(Restaurant).filter(Restaurant.owner_user_id == current_user.id).all()
    return UserOut(
        user_id=current_user.id,
        email=current_user.email,
        restaurants=[RestaurantOut.model_validate(r) for r in restaurants],
    )


@router.post("/restaurants", status_code=status.HTTP_201_CREATED, response_model=RestaurantOut)
def create_restaurant(
    payload: RestaurantCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    restaurant = Restaurant(name=payload.name, owner_user_id=current_user.id)
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return RestaurantOut.model_validate(restaurant)
