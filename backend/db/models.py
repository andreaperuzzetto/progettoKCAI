import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import DATE, TEXT, JSON, Uuid, Integer, Float, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.database import Base

# native_uuid=False stores as CHAR(32), compatible with both PostgreSQL and SQLite
PK_UUID = Uuid(as_uuid=True, native_uuid=False)
FK_UUID = Uuid(as_uuid=True, native_uuid=False)


# ── Phase 5: Organizations ─────────────────────────────────────────────────────

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    subscription_status: Mapped[str] = mapped_column(String(20), default="trial", nullable=False)
    plan: Mapped[str] = mapped_column(String(20), default="starter", nullable=False)
    trial_ends_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(FK_UUID, ForeignKey("organizations.id"), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="admin", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    owner_user_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("users.id"), nullable=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(FK_UUID, ForeignKey("organizations.id"), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
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
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
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
    product_predictions: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ── Phase 4: Alerts & Integrations ────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("restaurants.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    message: Mapped[str] = mapped_column(TEXT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class CorrelationResult(Base):
    __tablename__ = "correlation_results"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("restaurants.id"), nullable=False)
    correlations: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Integration(Base):
    __tablename__ = "integrations"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("restaurants.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ── Phase 5: AI Insights, Menu, Operations ────────────────────────────────────

class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("restaurants.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(TEXT, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    impact: Mapped[float] = mapped_column(Float, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ProductMetrics(Base):
    __tablename__ = "product_metrics"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("restaurants.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    total_quantity: Mapped[int] = mapped_column(Integer, default=0)
    total_revenue: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    avg_daily_qty: Mapped[float] = mapped_column(Float, default=0)
    trend_7d: Mapped[float] = mapped_column(Float, default=0)
    popularity_score: Mapped[float] = mapped_column(Float, default=0)
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("restaurants.id"), nullable=False)
    for_date: Mapped[date] = mapped_column(DATE, nullable=False)
    items: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MarketMetrics(Base):
    __tablename__ = "market_metrics"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avg_sentiment_positive: Mapped[float] = mapped_column(Float, default=0)
    avg_rating: Mapped[float] = mapped_column(Float, default=0)
    top_issues: Mapped[list] = mapped_column(JSON, default=list)
    restaurant_count: Mapped[int] = mapped_column(Integer, default=0)
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
