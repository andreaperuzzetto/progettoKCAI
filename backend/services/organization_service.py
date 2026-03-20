"""Organization service: multi-location management."""
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.db.models import Organization, User, Restaurant, Sales, AnalysisResult, Forecast


def create_organization(db: Session, owner: User, name: str) -> dict:
    org = Organization(name=name)
    db.add(org)
    db.flush()  # ensure org.id is assigned before linking user
    # Assign creator as admin
    owner.organization_id = org.id
    owner.role = "admin"
    db.commit()
    db.refresh(org)
    return _serialize(org)


def get_user_organization(db: Session, user: User) -> dict | None:
    if not user.organization_id:
        return None
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    if not org:
        return None
    restaurants = db.query(Restaurant).filter(Restaurant.organization_id == org.id).all()
    return {
        **_serialize(org),
        "restaurants": [{"id": str(r.id), "name": r.name, "city": r.city, "category": r.category} for r in restaurants],
        "your_role": user.role,
    }


def add_restaurant_to_org(db: Session, user: User, restaurant_id: uuid.UUID) -> dict:
    if not user.organization_id or user.role not in ("admin",):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Solo gli admin possono gestire l'organizzazione")
    r = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id,
        Restaurant.owner_user_id == user.id,
    ).first()
    if not r:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Ristorante non trovato")
    r.organization_id = user.organization_id
    db.commit()
    return {"restaurant_id": str(r.id), "organization_id": str(user.organization_id)}


def compare_locations(db: Session, organization_id: uuid.UUID) -> dict:
    """Return cross-restaurant comparison metrics for multi-location orgs."""
    restaurants = db.query(Restaurant).filter(
        Restaurant.organization_id == organization_id,
    ).all()

    if len(restaurants) < 2:
        return {"message": "Aggiungi almeno 2 ristoranti all'organizzazione per confrontarli.", "locations": []}

    from datetime import date, timedelta
    last30 = date.today() - timedelta(days=30)
    locations = []

    for r in restaurants:
        # Sales volume
        sales = db.query(Sales).filter(Sales.restaurant_id == r.id, Sales.date >= last30).all()
        total_qty = sum(s.quantity for s in sales)
        total_rev = sum(float(s.revenue or 0) for s in sales)

        # Sentiment
        analysis = db.query(AnalysisResult).filter(
            AnalysisResult.restaurant_id == r.id
        ).order_by(AnalysisResult.created_at.desc()).first()
        sentiment = analysis.sentiment_positive if analysis else None
        issues = analysis.issues[:2] if analysis else []

        # Forecast accuracy proxy
        fc_count = db.query(Forecast).filter(Forecast.restaurant_id == r.id).count()

        locations.append({
            "restaurant_id": str(r.id),
            "name": r.name,
            "city": r.city,
            "sales_30d": total_qty,
            "revenue_30d": round(total_rev, 2),
            "sentiment_positive": sentiment,
            "top_issues": [i.get("name") for i in issues],
            "forecast_available": fc_count > 0,
        })

    # Rank by revenue
    locations.sort(key=lambda x: x["revenue_30d"], reverse=True)
    for i, loc in enumerate(locations):
        loc["rank"] = i + 1

    return {"locations": locations, "restaurant_count": len(locations)}


def get_market_benchmark(db: Session, restaurant_id: uuid.UUID) -> dict:
    """Compare a restaurant's metrics against anonymized market averages."""
    from backend.db.models import MarketMetrics
    from datetime import date, timedelta

    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not r or not r.city:
        return {"message": "Imposta la città del ristorante per vedere i benchmark di mercato."}

    market = db.query(MarketMetrics).filter(
        MarketMetrics.city == r.city,
    ).order_by(MarketMetrics.computed_at.desc()).first()

    # Latest restaurant analysis
    analysis = db.query(AnalysisResult).filter(
        AnalysisResult.restaurant_id == restaurant_id
    ).order_by(AnalysisResult.created_at.desc()).first()

    restaurant_sentiment = analysis.sentiment_positive if analysis else None

    if not market:
        # Trigger computation now
        _recompute_market_metrics(db, r.city)
        market = db.query(MarketMetrics).filter(MarketMetrics.city == r.city).order_by(MarketMetrics.computed_at.desc()).first()

    if not market:
        return {"message": "Dati benchmark non ancora disponibili per questa città."}

    result = {
        "city": r.city,
        "market_avg_sentiment": market.avg_sentiment_positive,
        "market_avg_rating": market.avg_rating,
        "market_top_issues": market.top_issues,
        "restaurant_count_in_city": market.restaurant_count,
    }

    if restaurant_sentiment is not None:
        diff = restaurant_sentiment - market.avg_sentiment_positive
        result["your_sentiment"] = restaurant_sentiment
        result["vs_market"] = round(diff, 1)
        result["vs_market_label"] = (
            f"+{round(diff)}% sopra la media città" if diff > 2
            else f"{round(diff)}% sotto la media città" if diff < -2
            else "In linea con la media città"
        )

    return result


def _recompute_market_metrics(db: Session, city: str) -> None:
    """Aggregate anonymized metrics for a city."""
    from backend.db.models import MarketMetrics
    from collections import Counter

    restaurants = db.query(Restaurant).filter(Restaurant.city == city).all()
    if not restaurants:
        return

    sentiments, ratings, all_issues = [], [], []
    for r in restaurants:
        a = db.query(AnalysisResult).filter(
            AnalysisResult.restaurant_id == r.id
        ).order_by(AnalysisResult.created_at.desc()).first()
        if a:
            if a.sentiment_positive:
                sentiments.append(a.sentiment_positive)
            for issue in (a.issues or []):
                all_issues.append(issue.get("name", ""))

    if not sentiments:
        return

    avg_s = sum(sentiments) / len(sentiments)
    issue_counts = Counter(all_issues)
    top_issues = [name for name, _ in issue_counts.most_common(3)]

    existing = db.query(MarketMetrics).filter(MarketMetrics.city == city).first()
    if existing:
        existing.avg_sentiment_positive = avg_s
        existing.top_issues = top_issues
        existing.restaurant_count = len(restaurants)
        existing.computed_at = __import__("datetime").datetime.utcnow()
    else:
        db.add(MarketMetrics(
            city=city,
            avg_sentiment_positive=avg_s,
            avg_rating=0,
            top_issues=top_issues,
            restaurant_count=len(restaurants),
        ))
    db.commit()


def _serialize(org: Organization) -> dict:
    return {"id": str(org.id), "name": org.name, "created_at": str(org.created_at)}
