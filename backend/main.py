from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.config import settings
from backend.db.database import engine
from backend.db.models import Base

from backend.api.auth import router as auth_router
from backend.api.health import router as health_router
from backend.api.restaurants import router as restaurants_router
from backend.api.reviews import router as reviews_router
from backend.api.analysis import router as analysis_router
from backend.api.billing import router as billing_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


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
