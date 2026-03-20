import uuid
from datetime import date, datetime

from sqlalchemy import DATE, TEXT, Uuid, Integer, String, DateTime, ForeignKey
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    owner_user_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("users.id"), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Sales(Base):
    __tablename__ = "sales"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("restaurants.id"))
    date: Mapped[date] = mapped_column(DATE)
    product: Mapped[str] = mapped_column(TEXT)
    quantity: Mapped[int] = mapped_column(Integer)


class Reviews(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("restaurants.id"))
    date: Mapped[date] = mapped_column(DATE)
    platform: Mapped[str] = mapped_column(TEXT)
    review_text: Mapped[str] = mapped_column(TEXT)
    sentiment: Mapped[str] = mapped_column(TEXT, nullable=True)


class Forecast(Base):
    __tablename__ = "forecasts"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("restaurants.id"))
    date: Mapped[date] = mapped_column(DATE)
    product: Mapped[str] = mapped_column(TEXT)
    predicted_quantity: Mapped[int] = mapped_column(Integer)


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id: Mapped[uuid.UUID] = mapped_column(PK_UUID, default=uuid.uuid4, primary_key=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(FK_UUID, ForeignKey("restaurants.id"))
    date: Mapped[date] = mapped_column(DATE)
    forecast_summary: Mapped[str] = mapped_column(TEXT)
    issues: Mapped[str] = mapped_column(TEXT)
    suggestions: Mapped[str] = mapped_column(TEXT)
