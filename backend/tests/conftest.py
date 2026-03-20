import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db.database import Base, get_db
from backend.db.models import Restaurant, User
from backend.auth.utils import hash_password, create_access_token
from backend.main import app


@pytest.fixture()
def db_session():
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    """FastAPI test client wired to the in-memory database."""
    from fastapi.testclient import TestClient

    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def user(db_session):
    """Create a test user and return it."""
    u = User(
        email="test@example.com",
        password_hash=hash_password("testpassword"),
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture()
def restaurant(db_session, user):
    """Create a test restaurant owned by the test user and return its UUID."""
    rid = uuid.uuid4()
    r = Restaurant(id=rid, name="Test Restaurant", owner_user_id=user.id)
    db_session.add(r)
    db_session.commit()
    return rid


@pytest.fixture()
def auth_headers(user):
    """Return Authorization headers for the test user."""
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}
