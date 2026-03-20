import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.auth.utils import create_access_token, hash_password
from backend.db.database import Base, get_db
from backend.db.models import Restaurant, User
from backend.main import app

MOCK_LLM_RESPONSE = {
    "sentiment": {"positive_percentage": 60, "negative_percentage": 30},
    "issues": [{"name": "slow service", "frequency": 3}],
    "strengths": [{"name": "buon cibo", "frequency": 5}],
    "suggestions": [{"problem": "slow service", "action": "aggiungi 1 cameriere nelle fasce 20-22"}],
}


@pytest.fixture()
def db_session():
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
    from fastapi.testclient import TestClient

    app.dependency_overrides[get_db] = lambda: db_session
    with patch("ai.llm_analysis.call_llm", return_value=MOCK_LLM_RESPONSE):
        yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def user(db_session):
    u = User(
        email="test@example.com",
        password_hash=hash_password("testpassword"),
        subscription_status="active",
        plan="premium",
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture()
def restaurant(db_session, user):
    rid = uuid.uuid4()
    r = Restaurant(id=rid, name="Test Restaurant", owner_user_id=user.id)
    db_session.add(r)
    db_session.commit()
    return rid


@pytest.fixture()
def auth_headers(user):
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}
