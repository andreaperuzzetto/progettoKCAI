import uuid
from datetime import date, datetime

from sqlalchemy import DATE, TEXT, JSON, Uuid, Integer, Float, String, DateTime, ForeignKey
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
