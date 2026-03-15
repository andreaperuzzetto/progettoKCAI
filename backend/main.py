from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.health import router as health_router
from backend.api.sales import router as sales_router
from backend.api.reviews import router as reviews_router
from backend.api.forecast import router as forecast_router
from backend.api.review_analysis import router as review_analysis_router
from backend.api.correlation import router as correlation_router
from backend.api.daily_report import router as daily_report_router
from backend.config import settings

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(sales_router)
app.include_router(reviews_router)
app.include_router(forecast_router)
app.include_router(review_analysis_router)
app.include_router(correlation_router)
app.include_router(daily_report_router)
