"""Integration tests for the MVP review analysis pipeline."""

from backend.db.models import Reviews, AnalysisResult, UsageLog


REVIEWS_CSV = (
    "date,platform,review_text,rating\n"
    '2025-01-06,google,"il servizio era molto lento",2\n'
    '2025-01-07,tripadvisor,"ottimo cibo, tiramisu fantastico",5\n'
    '2025-01-08,google,"cibo freddo e cameriere scortese",1\n'
)


# ── Auth ──────────────────────────────────────────────────────────────

def test_register(client, db_session):
    resp = client.post("/auth/register", json={"email": "new@example.com", "password": "pass123"})
    assert resp.status_code == 201
    assert "access_token" in resp.json()

    log = db_session.query(UsageLog).filter(UsageLog.action == "register").first()
    assert log is not None


def test_login(client, user):
    resp = client.post("/auth/login", json={"email": "test@example.com", "password": "testpassword"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_me_returns_subscription_status(client, auth_headers, restaurant):
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["subscription_status"] == "active"
    assert len(data["restaurants"]) == 1


# ── Restaurants ───────────────────────────────────────────────────────

def test_list_restaurants(client, auth_headers, restaurant):
    resp = client.get("/restaurants", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_restaurant(client, auth_headers, restaurant):
    resp = client.get(f"/restaurants/{restaurant}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test Restaurant"


def test_get_restaurant_not_owned(client, auth_headers, db_session):
    import uuid
    fake_id = uuid.uuid4()
    resp = client.get(f"/restaurants/{fake_id}", headers=auth_headers)
    assert resp.status_code == 404


# ── Reviews upload ────────────────────────────────────────────────────

def test_upload_reviews_csv(client, restaurant, auth_headers, db_session):
    resp = client.post(
        "/reviews/upload",
        params={"restaurant_id": restaurant},
        files={"file": ("reviews.csv", REVIEWS_CSV.encode(), "text/csv")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["rows_imported"] == 3

    rows = db_session.query(Reviews).filter(Reviews.restaurant_id == restaurant).all()
    assert len(rows) == 3
    assert rows[0].rating == 2
    assert rows[1].rating == 5

    log = db_session.query(UsageLog).filter(UsageLog.action == "upload_reviews").first()
    assert log is not None


def test_upload_reviews_dedup(client, restaurant, auth_headers, db_session):
    for _ in range(2):
        client.post(
            "/reviews/upload",
            params={"restaurant_id": restaurant},
            files={"file": ("reviews.csv", REVIEWS_CSV.encode(), "text/csv")},
            headers=auth_headers,
        )
    rows = db_session.query(Reviews).filter(Reviews.restaurant_id == restaurant).all()
    assert len(rows) == 3  # no duplicates


def test_upload_reviews_text(client, restaurant, auth_headers, db_session):
    resp = client.post(
        "/reviews/upload-text",
        params={"restaurant_id": restaurant},
        json={"reviews": ["ottimo posto!", "servizio lento ma cibo buono"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["rows_imported"] == 2


def test_upload_requires_auth(client, restaurant):
    resp = client.post(
        "/reviews/upload",
        params={"restaurant_id": restaurant},
        files={"file": ("reviews.csv", REVIEWS_CSV.encode(), "text/csv")},
    )
    assert resp.status_code in (401, 403)


# ── Analysis ──────────────────────────────────────────────────────────

def test_run_analysis(client, restaurant, auth_headers, db_session):
    client.post(
        "/reviews/upload",
        params={"restaurant_id": restaurant},
        files={"file": ("reviews.csv", REVIEWS_CSV.encode(), "text/csv")},
        headers=auth_headers,
    )

    resp = client.post(
        "/analysis/run",
        params={"restaurant_id": restaurant},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"

    sentiment = data["sentiment"]
    assert "positive_percentage" in sentiment
    assert "negative_percentage" in sentiment

    assert isinstance(data["issues"], list)
    assert isinstance(data["strengths"], list)
    assert isinstance(data["suggestions"], list)

    result = db_session.query(AnalysisResult).filter(
        AnalysisResult.restaurant_id == restaurant
    ).first()
    assert result is not None

    log = db_session.query(UsageLog).filter(UsageLog.action == "run_analysis").first()
    assert log is not None


def test_get_latest_analysis(client, restaurant, auth_headers, db_session):
    client.post(
        "/reviews/upload",
        params={"restaurant_id": restaurant},
        files={"file": ("reviews.csv", REVIEWS_CSV.encode(), "text/csv")},
        headers=auth_headers,
    )
    client.post(
        "/analysis/run",
        params={"restaurant_id": restaurant},
        headers=auth_headers,
    )

    resp = client.get(
        "/analysis/latest",
        params={"restaurant_id": restaurant},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["analysis"] is not None
    assert data["analysis"]["sentiment"]["positive_percentage"] == 60

    log = db_session.query(UsageLog).filter(UsageLog.action == "view_dashboard").first()
    assert log is not None


def test_get_latest_empty(client, restaurant, auth_headers):
    resp = client.get(
        "/analysis/latest",
        params={"restaurant_id": restaurant},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["analysis"] is None


def test_analysis_requires_subscription(client, restaurant, auth_headers, db_session, user):
    user.subscription_status = "inactive"
    db_session.commit()

    resp = client.post(
        "/analysis/run",
        params={"restaurant_id": restaurant},
        headers=auth_headers,
    )
    assert resp.status_code == 402


# ── Sales ─────────────────────────────────────────────────────────────

SALES_CSV = (
    "date,product,quantity\n"
    "2025-01-01,pizza margherita,10\n"
    "2025-01-01,birra,15\n"
    "2025-01-02,pizza margherita,12\n"
    "2025-01-03,pizza margherita,8\n"
    "2025-01-04,pizza margherita,11\n"
    "2025-01-05,birra,20\n"
    "2025-01-06,pizza margherita,9\n"
    "2025-01-07,pizza margherita,13\n"
)


def test_upload_sales_csv(client, restaurant, auth_headers, db_session):
    from backend.db.models import Sales
    resp = client.post(
        "/sales/upload",
        params={"restaurant_id": restaurant},
        files={"file": ("sales.csv", SALES_CSV.encode(), "text/csv")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["inserted"] == 8
    rows = db_session.query(Sales).filter(Sales.restaurant_id == restaurant).all()
    assert len(rows) == 8


def test_upload_sales_dedup(client, restaurant, auth_headers, db_session):
    from backend.db.models import Sales
    for _ in range(2):
        client.post(
            "/sales/upload",
            params={"restaurant_id": restaurant},
            files={"file": ("sales.csv", SALES_CSV.encode(), "text/csv")},
            headers=auth_headers,
        )
    rows = db_session.query(Sales).filter(Sales.restaurant_id == restaurant).all()
    assert len(rows) == 8  # no duplicates


def test_sales_summary(client, restaurant, auth_headers):
    client.post(
        "/sales/upload",
        params={"restaurant_id": restaurant},
        files={"file": ("sales.csv", SALES_CSV.encode(), "text/csv")},
        headers=auth_headers,
    )
    resp = client.get("/sales/summary", params={"restaurant_id": restaurant, "days": 500}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_records"] == 8
    assert data["top_products"][0]["name"] == "pizza margherita"


# ── Products & Ingredients ────────────────────────────────────────────

def test_create_product_and_ingredient(client, restaurant, auth_headers):
    resp = client.post(
        "/products",
        params={"restaurant_id": restaurant},
        json={"name": "Pizza Margherita", "category": "pizza"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    product_id = resp.json()["id"]

    resp = client.post(
        "/ingredients",
        params={"restaurant_id": restaurant},
        json={"name": "Mozzarella", "unit": "kg"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    ing_id = resp.json()["id"]

    resp = client.post(
        f"/products/{product_id}/ingredients",
        params={"restaurant_id": restaurant},
        json=[{"ingredient_id": ing_id, "quantity_per_unit": 0.15}],
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["mappings_set"] == 1


def test_list_products(client, restaurant, auth_headers):
    client.post(
        "/products",
        params={"restaurant_id": restaurant},
        json={"name": "Tiramisu", "category": "dolci"},
        headers=auth_headers,
    )
    resp = client.get("/products", params={"restaurant_id": restaurant}, headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# ── Forecast ──────────────────────────────────────────────────────────

def test_generate_forecast(client, restaurant, auth_headers):
    # Upload some sales data first
    client.post(
        "/sales/upload",
        params={"restaurant_id": restaurant},
        files={"file": ("sales.csv", SALES_CSV.encode(), "text/csv")},
        headers=auth_headers,
    )
    resp = client.post("/forecast/generate", params={"restaurant_id": restaurant}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["generated"] == 7
    assert len(data["forecasts"]) == 7


def test_forecast_without_data_returns_zeros(client, restaurant, auth_headers):
    resp = client.post("/forecast/generate", params={"restaurant_id": restaurant}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["generated"] == 7
    # No data → expected_covers should be 0
    assert all(f["expected_covers"] == 0 for f in data["forecasts"])


# ── Daily report ──────────────────────────────────────────────────────

def test_daily_report(client, restaurant, auth_headers):
    resp = client.get("/daily-report", params={"restaurant_id": restaurant}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "tomorrow" in data
    assert "suggestions" in data
    assert "review_summary" in data
    assert "forecast_7days" in data
