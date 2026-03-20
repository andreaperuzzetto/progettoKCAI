"""Menu optimization service."""
import uuid
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.db.models import Sales, ProductMetrics
from ai.menu_optimizer import analyze_menu


def compute_product_metrics(db: Session, restaurant_id: uuid.UUID) -> list[dict]:
    """Aggregate sales data into product metrics and upsert ProductMetrics table."""
    today = date.today()
    last30 = today - timedelta(days=30)
    last7 = today - timedelta(days=7)
    prev7 = today - timedelta(days=14)

    # Total quantities and revenue per product (last 30 days)
    rows = db.query(Sales).filter(
        Sales.restaurant_id == restaurant_id,
        Sales.date >= last30,
    ).all()

    if not rows:
        return []

    from collections import defaultdict
    stats: dict[str, dict] = defaultdict(lambda: {"qty30": 0, "rev30": 0.0, "qty7": 0, "qty_prev7": 0})
    for r in rows:
        n = r.product_name
        stats[n]["qty30"] += r.quantity
        stats[n]["rev30"] += float(r.revenue or 0)
        if r.date >= last7:
            stats[n]["qty7"] += r.quantity
        elif r.date >= prev7:
            stats[n]["qty_prev7"] += r.quantity

    total_qty = sum(s["qty30"] for s in stats.values())

    metrics = []
    for name, s in stats.items():
        avg_daily = s["qty30"] / 30
        pop_score = s["qty30"] / total_qty if total_qty > 0 else 0
        trend = 0.0
        if s["qty_prev7"] > 0:
            trend = (s["qty7"] - s["qty_prev7"]) / s["qty_prev7"] * 100

        # Upsert
        pm = db.query(ProductMetrics).filter(
            ProductMetrics.restaurant_id == restaurant_id,
            ProductMetrics.product_name == name,
        ).first()
        if pm:
            pm.total_quantity = s["qty30"]
            pm.total_revenue = s["rev30"]
            pm.avg_daily_qty = avg_daily
            pm.trend_7d = trend
            pm.popularity_score = pop_score
            pm.computed_at = date.today()
        else:
            pm = ProductMetrics(
                restaurant_id=restaurant_id,
                product_name=name,
                total_quantity=s["qty30"],
                total_revenue=s["rev30"],
                avg_daily_qty=avg_daily,
                trend_7d=trend,
                popularity_score=pop_score,
            )
            db.add(pm)

        metrics.append({
            "product_name": name,
            "total_quantity": s["qty30"],
            "total_revenue": s["rev30"],
            "avg_daily_qty": round(avg_daily, 1),
            "trend_7d": round(trend, 1),
            "popularity_score": round(pop_score, 3),
        })

    db.commit()
    return metrics


def get_menu_suggestions(db: Session, restaurant_id: uuid.UUID) -> dict:
    """Compute product metrics and return menu optimization suggestions."""
    metrics = compute_product_metrics(db, restaurant_id)
    if not metrics:
        return {"suggestions": [], "message": "Nessun dato vendite disponibile. Carica le vendite prima."}
    suggestions = analyze_menu(metrics)
    return {"suggestions": suggestions, "product_count": len(metrics)}
