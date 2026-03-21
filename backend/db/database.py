from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import settings


def _build_engine():
    url = settings.database_url
    kwargs: dict = {
        "pool_pre_ping": True,      # reconnect on stale connections
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,       # recycle connections every 30 min
    }

    # Supabase (and any PostgreSQL URL with sslmode) requires SSL.
    # psycopg2 accepts sslmode in the URL query string; we also set
    # connect_args as a fallback for URLs that omit it.
    is_postgres = url.startswith("postgresql") or url.startswith("postgres")
    if is_postgres and "sslmode" not in url:
        # If the URL doesn't already carry sslmode, add require for safety.
        # Local connections (localhost / 127.0.0.1) work fine without SSL.
        is_local = "localhost" in url or "127.0.0.1" in url
        if not is_local:
            kwargs["connect_args"] = {"sslmode": "require"}

    return create_engine(url, **kwargs)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
