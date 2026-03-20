import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.auth.utils import create_access_token, hash_password, verify_password
from backend.db.database import get_db
from backend.db.models import Restaurant, User
from backend.services.usage_service import log_action

router = APIRouter(prefix="/auth", tags=["auth"])
_limiter = Limiter(key_func=get_remote_address)

TRIAL_DAYS = 7


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
    subscription_status: str
    plan: str
    restaurants: list[RestaurantOut]


# --- Routes ---

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    trial_ends = datetime.now(timezone.utc) + timedelta(days=TRIAL_DAYS)
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        subscription_status="trial",
        trial_ends_at=trial_ends,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_action(user.id, "register", db)
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
@_limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Expire trial if needed
    if user.subscription_status == "trial" and user.trial_ends_at:
        if datetime.now(timezone.utc) > user.trial_ends_at.replace(tzinfo=timezone.utc):
            user.subscription_status = "inactive"
            db.commit()

    log_action(user.id, "login", db)
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    restaurants = db.query(Restaurant).filter(Restaurant.owner_user_id == current_user.id).all()
    return UserOut(
        user_id=current_user.id,
        email=current_user.email,
        subscription_status=current_user.subscription_status,
        plan=getattr(current_user, "plan", "starter") or "starter",
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
