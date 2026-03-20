import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import DATE, TEXT, JSON, Uuid, Integer, Float, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.database import Base

# native_uuid=False stores as CHAR(32), compatible with both PostgreSQL and SQLite
PK_UUID = Uuid(as_uuid=True, native_uuid=False)
FK_UUID = Uuid(as_uuid=True, native_uuid=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    subscription_status: Mapped[str] = mapped_column(String(20), default="trial", nullable=False)
    trial_ends_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    owner_user_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Reviews(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("restaurants.id"))
    review_text: Mapped[str] = mapped_column(TEXT)
    rating: Mapped[int] = mapped_column(Integer, nullable=True)
    date: Mapped[date] = mapped_column(DATE, nullable=True)
    platform: Mapped[str] = mapped_column(TEXT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("restaurants.id"))
    period: Mapped[str] = mapped_column(String(50), default="all")
    sentiment_positive: Mapped[float] = mapped_column(Float, nullable=True)
    sentiment_negative: Mapped[float] = mapped_column(Float, nullable=True)
    issues: Mapped[list] = mapped_column(JSON, default=list)
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    suggestions: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ── Phase 3: Operational Data ──────────────────────────────────────────────────

class Sales(Base):
    __tablename__ = "sales"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("restaurants.id"), nullable=False)
    date: Mapped[date] = mapped_column(DATE, nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    revenue: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("restaurants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("restaurants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # kg, pezzi, litri…
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProductIngredient(Base):
    __tablename__ = "product_ingredients"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    product_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("products.id"), nullable=False)
    ingredient_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("ingredients.id"), nullable=False)
    quantity_per_unit: Mapped[float] = mapped_column(Float, nullable=False)


class Forecast(Base):
    __tablename__ = "forecasts"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("restaurants.id"), nullable=False)
    date: Mapped[date] = mapped_column(DATE, nullable=False)
    expected_covers: Mapped[int] = mapped_column(Integer, nullable=False)
    product_predictions: Mapped[dict] = mapped_column(JSON, default=dict)  # {product_name: qty}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
