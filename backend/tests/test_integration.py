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


# ── Alerts ────────────────────────────────────────────────────────────

def test_generate_alerts_no_data(client, restaurant, auth_headers):
    """With no data, no alerts should be triggered."""
    resp = client.post("/alerts/generate", params={"restaurant_id": restaurant}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "generated" in data
    assert "alerts" in data
    # No data → no alerts (or some alerts like low_sentiment if analysis exists)
    assert isinstance(data["alerts"], list)


def test_generate_alerts_with_high_demand(client, restaurant, auth_headers, db_session):
    """With enough sales + forecast, high demand alert may fire."""
    # Upload sales and generate forecast
    client.post(
        "/sales/upload",
        params={"restaurant_id": restaurant},
        files={"file": ("sales.csv", SALES_CSV.encode(), "text/csv")},
        headers=auth_headers,
    )
    client.post("/forecast/generate", params={"restaurant_id": restaurant}, headers=auth_headers)

    resp = client.post("/alerts/generate", params={"restaurant_id": restaurant}, headers=auth_headers)
    assert resp.status_code == 200


def test_get_alerts(client, restaurant, auth_headers):
    client.post("/alerts/generate", params={"restaurant_id": restaurant}, headers=auth_headers)
    resp = client.get("/alerts", params={"restaurant_id": restaurant}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "alerts" in data
    assert "unread_count" in data


def test_mark_alert_read(client, restaurant, auth_headers, db_session):
    from backend.db.models import Alert
    import uuid as _uuid
    # Create an alert directly
    alert = Alert(
        id=_uuid.uuid4(),
        restaurant_id=restaurant,
        type="test",
        severity="low",
        message="Test alert",
    )
    db_session.add(alert)
    db_session.commit()

    resp = client.post(f"/alerts/{alert.id}/read", params={"restaurant_id": restaurant}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["read"] is True


# ── Correlations V2 ───────────────────────────────────────────────────

def test_run_correlation(client, restaurant, auth_headers):
    """Should run (with rule-based fallback) and return list."""
    resp = client.post("/correlations/run", params={"restaurant_id": restaurant}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "correlations" in data
    assert isinstance(data["correlations"], list)


def test_get_latest_correlation_empty(client, restaurant, auth_headers):
    resp = client.get("/correlations/latest", params={"restaurant_id": restaurant}, headers=auth_headers)
    assert resp.status_code == 200
    assert "correlations" in resp.json()


# ── Integrations ──────────────────────────────────────────────────────

def test_create_integration(client, restaurant, auth_headers):
    resp = client.post(
        "/integrations",
        params={"restaurant_id": restaurant},
        json={"provider": "csv_auto", "config": {"file_path": "/tmp/nonexistent.csv"}},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "csv_auto"
    assert data["status"] == "pending"


def test_create_integration_invalid_provider(client, restaurant, auth_headers):
    resp = client.post(
        "/integrations",
        params={"restaurant_id": restaurant},
        json={"provider": "nonexistent_pos"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_list_integrations(client, restaurant, auth_headers):
    client.post(
        "/integrations",
        params={"restaurant_id": restaurant},
        json={"provider": "square", "config": {"access_token": "test-token"}},
        headers=auth_headers,
    )
    resp = client.get("/integrations", params={"restaurant_id": restaurant}, headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    # Sensitive fields should be masked
    config = items[0].get("config", {})
    if "access_token" in config:
        assert config["access_token"] == "***"


def test_sync_integration_provider_error(client, restaurant, auth_headers, db_session):
    """Square sync with missing token returns 502."""
    resp_create = client.post(
        "/integrations",
        params={"restaurant_id": restaurant},
        json={"provider": "square", "config": {}},
        headers=auth_headers,
    )
    int_id = resp_create.json()["id"]

    resp = client.post(
        f"/integrations/{int_id}/sync",
        params={"restaurant_id": restaurant},
        headers=auth_headers,
    )
    assert resp.status_code == 502


# ── Plan feature gating ───────────────────────────────────────────────

def test_plan_defaults_to_starter(client, auth_headers, user):
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "plan" in data


# ── Phase 5: Organizations ─────────────────────────────────────────────────────

def test_create_organization(client, auth_headers):
    resp = client.post("/organizations", json={"name": "My Restaurant Group"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "My Restaurant Group"
    assert "id" in data


def test_get_my_org(client, auth_headers):
    client.post("/organizations", json={"name": "Gruppo Test"}, headers=auth_headers)
    resp = client.get("/organizations/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Gruppo Test"
    assert "your_role" in data
    assert data["your_role"] == "admin"


def test_get_my_org_no_org(client, auth_headers):
    resp = client.get("/organizations/me", headers=auth_headers)
    assert resp.status_code == 404


def test_compare_no_org(client, auth_headers):
    resp = client.get("/organizations/compare", headers=auth_headers)
    assert resp.status_code == 404


def test_compare_single_location(client, auth_headers, restaurant):
    client.post("/organizations", json={"name": "Group"}, headers=auth_headers)
    client.post(f"/organizations/restaurants/{restaurant}", headers=auth_headers)
    resp = client.get("/organizations/compare", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data  # not enough locations


def test_benchmark_no_city(client, auth_headers, restaurant):
    resp = client.get(f"/organizations/benchmark?restaurant_id={restaurant}", headers=auth_headers)
    assert resp.status_code == 200
    assert "message" in resp.json()


# ── Phase 5: Insights ──────────────────────────────────────────────────────────

def test_generate_insights_empty(client, auth_headers, restaurant):
    resp = client.post(f"/insights/generate?restaurant_id={restaurant}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "insights" in data
    assert isinstance(data["insights"], list)


def test_get_insights_latest(client, auth_headers, restaurant):
    client.post(f"/insights/generate?restaurant_id={restaurant}", headers=auth_headers)
    resp = client.get(f"/insights/latest?restaurant_id={restaurant}", headers=auth_headers)
    assert resp.status_code == 200
    assert "insights" in resp.json()


# ── Phase 5: Menu Optimization ────────────────────────────────────────────────

def _menu_csv():
    from datetime import date, timedelta
    today = date.today()
    rows = []
    for d in [today - timedelta(days=i) for i in range(1, 4)]:
        rows.append(f"{d},Pizza Margherita,20,200")
        rows.append(f"{d},Tiramisu,5,40")
        rows.append(f"{d},Acqua,30,30")
    return "date,product,quantity,revenue\n" + "\n".join(rows) + "\n"


SALES_CSV_MENU = _menu_csv()


def test_menu_analyze_no_data(client, auth_headers, restaurant):
    resp = client.post(f"/menu/analyze?restaurant_id={restaurant}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "suggestions" in data


def test_menu_analyze_with_data(client, auth_headers, restaurant):
    client.post(
        "/sales/upload",
        params={"restaurant_id": restaurant},
        files={"file": ("sales.csv", SALES_CSV_MENU.encode(), "text/csv")},
        headers=auth_headers,
    )
    resp = client.post(f"/menu/analyze?restaurant_id={restaurant}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["suggestions"]) > 0
    # Each suggestion has required fields
    for s in data["suggestions"]:
        assert "product" in s
        assert "action" in s
        assert "reason" in s


def test_menu_metrics(client, auth_headers, restaurant):
    client.post(
        "/sales/upload",
        params={"restaurant_id": restaurant},
        files={"file": ("sales.csv", SALES_CSV_MENU.encode(), "text/csv")},
        headers=auth_headers,
    )
    resp = client.get(f"/menu/metrics?restaurant_id={restaurant}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["count"] > 0


# ── Phase 5: Operations ───────────────────────────────────────────────────────

def test_purchase_order_no_forecast(client, auth_headers, restaurant):
    resp = client.post(f"/operations/purchase-order?restaurant_id={restaurant}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data or "items" in data


def test_staff_plan_no_forecast(client, auth_headers, restaurant):
    resp = client.get(f"/operations/staff-plan?restaurant_id={restaurant}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "days" in data


def test_staff_plan_with_forecast(client, auth_headers, restaurant, db_session):
    import uuid
    from datetime import date, timedelta
    from backend.db.models import Forecast
    for i in range(1, 8):
        fc = Forecast(
            restaurant_id=restaurant,
            date=date.today() + timedelta(days=i),
            expected_covers=40 + i * 2,
            product_predictions={"Pizza Margherita": 20},
        )
        db_session.add(fc)
    db_session.commit()

    resp = client.get(f"/operations/staff-plan?restaurant_id={restaurant}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["days"]) == 7
    day = data["days"][0]
    assert "shifts" in day
    assert "lunch" in day["shifts"]
    assert "dinner" in day["shifts"]


def test_list_purchase_orders(client, auth_headers, restaurant):
    resp = client.get(f"/operations/purchase-orders?restaurant_id={restaurant}", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ── Phase 5: Restaurant PATCH ──────────────────────────────────────────────────

def test_update_restaurant(client, auth_headers, restaurant):
    resp = client.patch(
        f"/restaurants/{restaurant}",
        json={"city": "Milano", "category": "pizza"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["city"] == "Milano"
    assert data["category"] == "pizza"
