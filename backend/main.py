from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.config import settings
from backend.db.database import engine, SessionLocal
from backend.db.models import Base, Restaurant, User

from backend.api.auth import router as auth_router
from backend.api.health import router as health_router
from backend.api.restaurants import router as restaurants_router
from backend.api.reviews import router as reviews_router
from backend.api.analysis import router as analysis_router
from backend.api.billing import router as billing_router
from backend.api.sales import router as sales_router
from backend.api.products import router as products_router
from backend.api.forecast import router as forecast_router
from backend.api.daily_report import router as daily_report_router
from backend.api.notifications import router as notifications_router

logger = logging.getLogger(__name__)


def _run_daily_forecasts():
    """Nightly job: regenerate forecasts for all restaurants."""
    from backend.services.forecast_service import run_forecast
    db = SessionLocal()
    try:
        restaurants = db.query(Restaurant).all()
        for r in restaurants:
            try:
                run_forecast(db, r.id)
                logger.info("Forecast generated for restaurant %s", r.id)
            except Exception as e:
                logger.error("Forecast failed for %s: %s", r.id, e)
    finally:
        db.close()


def _run_daily_emails():
    """Morning job: send daily briefing to all active users."""
    from backend.services.email_service import send_daily_email
    from backend.services.forecast_service import get_latest_forecast
    from backend.services.sales_service import get_sales_history
    from backend.services.products_service import get_all_product_ingredient_mappings
    from backend.services.analysis_service import get_latest as get_latest_analysis
    from ai.suggestions_engine import generate_all_suggestions
    from ai.correlation_engine import run_correlation

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.subscription_status.in_(["active", "trial"])).all()
        for user in users:
            restaurants = db.query(Restaurant).filter(Restaurant.owner_user_id == user.id).all()
            for restaurant in restaurants:
                try:
                    forecasts = get_latest_forecast(db, restaurant.id)
                    tomorrow = forecasts[0] if forecasts else {"expected_covers": 0, "product_predictions": {}}
                    historical = get_sales_history(db, restaurant.id, days=14)
                    avg_covers = sum(r["quantity"] for r in historical) / 14.0 if historical else 0.0
                    pim = get_all_product_ingredient_mappings(db, restaurant.id)
                    op_suggestions = generate_all_suggestions(forecasts, pim, historical, avg_covers)
                    analysis = get_latest_analysis(db, restaurant.id)
                    issues = analysis.issues if analysis else []
                    corr = run_correlation(issues, tomorrow)
                    report = {
                        "tomorrow": {
                            "expected_covers": tomorrow.get("expected_covers", 0),
                            "top_products": sorted(
                                [{"name": k, "predicted_qty": v} for k, v in (tomorrow.get("product_predictions") or {}).items() if v > 0],
                                key=lambda x: x["predicted_qty"], reverse=True
                            )[:5],
                        },
                        "suggestions": (corr + op_suggestions)[:5],
                        "review_summary": {"sentiment_positive": analysis.sentiment_positive if analysis else None},
                    }
                    send_daily_email(user.email, restaurant.name, report)
                except Exception as e:
                    logger.error("Daily email failed for user %s restaurant %s: %s", user.id, restaurant.id, e)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    # Start scheduler
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(_run_daily_forecasts, "cron", hour=2, minute=0, id="daily_forecast")
    scheduler.add_job(_run_daily_emails, "cron", hour=7, minute=0, id="daily_email")
    scheduler.start()
    logger.info("Scheduler started: forecast at 02:00, email at 07:00")

    yield

    scheduler.shutdown()


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(restaurants_router)
app.include_router(reviews_router)
app.include_router(analysis_router)
app.include_router(billing_router)
app.include_router(sales_router)
app.include_router(products_router)
app.include_router(forecast_router)
app.include_router(daily_report_router)
app.include_router(notifications_router)
