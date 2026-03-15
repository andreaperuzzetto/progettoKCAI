"""Phase 10 — End-to-end integration test.

Validates the full workflow:
1. Upload sales data
2. Upload reviews
3. Run forecast
4. Run correlation engine
5. Generate daily report

Verifies correct data storage, predictions, and suggestions.
"""

from backend.db.models import Sales, Reviews, Forecast, DailyReport


SALES_CSV = (
    "date,product,quantity\n"
    "2025-01-06,pizza,40\n"
    "2025-01-07,pizza,42\n"
    "2025-01-08,pizza,38\n"
    "2025-01-06,pasta,30\n"
    "2025-01-07,pasta,28\n"
    "2025-01-08,pasta,32\n"
)

REVIEWS_CSV = (
    "date,platform,review_text\n"
    '2025-01-06,google,"pizza was burnt"\n'
    '2025-01-07,tripadvisor,"great tiramisu"\n'
    '2025-01-08,google,"slow service, waited too long"\n'
)


# ── Step 1: Upload sales data ──────────────────────────────────────

def test_upload_sales(client, restaurant, db_session):
    resp = client.post(
        "/upload-sales",
        params={"restaurant_id": restaurant},
        files={"file": ("sales.csv", SALES_CSV.encode(), "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["rows_imported"] == 6

    # Verify data stored in DB
    rows = db_session.query(Sales).filter(Sales.restaurant_id == restaurant).all()
    assert len(rows) == 6
    products = {r.product for r in rows}
    assert products == {"pizza", "pasta"}


# ── Step 2: Upload reviews ─────────────────────────────────────────

def test_upload_reviews(client, restaurant, db_session):
    resp = client.post(
        "/upload-reviews",
        params={"restaurant_id": restaurant},
        files={"file": ("reviews.csv", REVIEWS_CSV.encode(), "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["rows_imported"] == 3

    # Verify data stored in DB
    rows = db_session.query(Reviews).filter(Reviews.restaurant_id == restaurant).all()
    assert len(rows) == 3
    # Sentiment is null before analysis
    assert all(r.sentiment is None for r in rows)


# ── Step 3: Run forecast ───────────────────────────────────────────

def test_forecast(client, restaurant, db_session):
    # Upload sales first
    client.post(
        "/upload-sales",
        params={"restaurant_id": restaurant},
        files={"file": ("sales.csv", SALES_CSV.encode(), "text/csv")},
    )

    resp = client.get(
        "/forecast",
        params={"restaurant_id": restaurant, "target_date": "2025-01-09"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["target_date"] == "2025-01-09"

    predictions = data["predictions"]
    assert "pizza" in predictions
    assert "pasta" in predictions
    assert predictions["pizza"] > 0
    assert predictions["pasta"] > 0

    # Verify stored in Forecast table
    rows = db_session.query(Forecast).filter(Forecast.restaurant_id == restaurant).all()
    assert len(rows) == 2
    stored_products = {r.product for r in rows}
    assert stored_products == {"pizza", "pasta"}


# ── Step 4: Run correlation engine ─────────────────────────────────

def test_correlation(client, restaurant, db_session):
    # Upload sales + reviews
    client.post(
        "/upload-sales",
        params={"restaurant_id": restaurant},
        files={"file": ("sales.csv", SALES_CSV.encode(), "text/csv")},
    )
    client.post(
        "/upload-reviews",
        params={"restaurant_id": restaurant},
        files={"file": ("reviews.csv", REVIEWS_CSV.encode(), "text/csv")},
    )

    # Run review analysis first to set sentiments
    client.get("/review-analysis", params={"restaurant_id": restaurant})

    resp = client.get("/correlation", params={"restaurant_id": restaurant})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"

    hypotheses = data["hypotheses"]
    assert len(hypotheses) > 0

    # Should detect burnt food and slow service from the reviews
    problems = {h["problem"] for h in hypotheses}
    assert "burnt food" in problems
    assert "slow service" in problems

    # Each hypothesis has required fields
    for h in hypotheses:
        assert "problem" in h
        assert "possible_cause" in h
        assert "suggested_action" in h
        assert "spike_detected" in h


# ── Step 5: Generate daily report ──────────────────────────────────

def test_daily_report(client, restaurant, db_session):
    # Upload sales + reviews
    client.post(
        "/upload-sales",
        params={"restaurant_id": restaurant},
        files={"file": ("sales.csv", SALES_CSV.encode(), "text/csv")},
    )
    client.post(
        "/upload-reviews",
        params={"restaurant_id": restaurant},
        files={"file": ("reviews.csv", REVIEWS_CSV.encode(), "text/csv")},
    )

    resp = client.get(
        "/daily-report",
        params={"restaurant_id": restaurant, "target_date": "2025-01-09"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["date"] == "2025-01-09"

    # Forecast present
    assert "forecast" in data
    assert "pizza" in data["forecast"]
    assert "pasta" in data["forecast"]

    # Sentiments present
    assert "sentiments" in data
    assert "negative" in data["sentiments"]
    assert "positive" in data["sentiments"]

    # Issues and suggestions present
    assert "issues" in data
    assert "suggestions" in data
    assert data["issues"] != "No issues detected."
    assert data["suggestions"] != "No suggestions at this time."

    # Verify DailyReport stored in DB
    rows = db_session.query(DailyReport).filter(
        DailyReport.restaurant_id == restaurant
    ).all()
    assert len(rows) == 1
    report = rows[0]
    assert "pizza" in report.forecast_summary.lower()
    assert report.issues != ""
    assert report.suggestions != ""

    # Verify review sentiments were updated
    reviews = db_session.query(Reviews).filter(
        Reviews.restaurant_id == restaurant
    ).all()
    sentiments = {r.sentiment for r in reviews}
    assert "negative" in sentiments
    assert "positive" in sentiments


# ── Full pipeline in one test ──────────────────────────────────────

def test_full_pipeline(client, restaurant, db_session):
    """Run the complete workflow end-to-end in sequence."""

    # 1. Upload sales
    resp = client.post(
        "/upload-sales",
        params={"restaurant_id": restaurant},
        files={"file": ("sales.csv", SALES_CSV.encode(), "text/csv")},
    )
    assert resp.json()["rows_imported"] == 6

    # 2. Upload reviews
    resp = client.post(
        "/upload-reviews",
        params={"restaurant_id": restaurant},
        files={"file": ("reviews.csv", REVIEWS_CSV.encode(), "text/csv")},
    )
    assert resp.json()["rows_imported"] == 3

    # 3. Forecast
    resp = client.get(
        "/forecast",
        params={"restaurant_id": restaurant, "target_date": "2025-01-09"},
    )
    predictions = resp.json()["predictions"]
    assert len(predictions) == 2

    # 4. Correlation
    resp = client.get("/correlation", params={"restaurant_id": restaurant})
    hypotheses = resp.json()["hypotheses"]
    assert len(hypotheses) > 0

    # 5. Daily report
    resp = client.get(
        "/daily-report",
        params={"restaurant_id": restaurant, "target_date": "2025-01-10"},
    )
    report = resp.json()
    assert report["status"] == "ok"
    assert len(report["forecast"]) == 2
    assert report["issues"] != "No issues detected."

    # Verify all tables have data
    assert db_session.query(Sales).count() == 6
    assert db_session.query(Reviews).count() == 3
    assert db_session.query(Forecast).count() == 4  # 2 from step 3 + 2 from step 5
    assert db_session.query(DailyReport).count() == 1
