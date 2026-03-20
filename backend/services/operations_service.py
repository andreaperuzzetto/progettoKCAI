"""Operations service: purchase orders and staff planning."""
import uuid
from datetime import date, timedelta
from sqlalchemy.orm import Session

from backend.db.models import (
    Forecast, Product, Ingredient, ProductIngredient, PurchaseOrder, Sales
)


def generate_purchase_order(db: Session, restaurant_id: uuid.UUID, for_date: date | None = None) -> dict:
    """Generate a purchase order based on tomorrow's forecast and ingredient mappings."""
    target = for_date or (date.today() + timedelta(days=1))

    fc = db.query(Forecast).filter(
        Forecast.restaurant_id == restaurant_id,
        Forecast.date == target,
    ).first()

    if not fc:
        return {
            "error": "Nessuna previsione disponibile per la data richiesta. Genera prima una previsione.",
            "items": [],
        }

    # Aggregate ingredient needs from product predictions
    product_preds: dict = fc.product_predictions or {}
    ingredient_totals: dict[str, dict] = {}

    for product_name, pred_qty in product_preds.items():
        # Find product by name
        product = db.query(Product).filter(
            Product.restaurant_id == restaurant_id,
            Product.name == product_name,
        ).first()
        if not product:
            continue

        # Get ingredient mappings
        mappings = db.query(ProductIngredient).filter(
            ProductIngredient.product_id == product.id,
        ).all()

        for m in mappings:
            ing = db.query(Ingredient).filter(Ingredient.id == m.ingredient_id).first()
            if not ing:
                continue
            key = str(ing.id)
            if key not in ingredient_totals:
                ingredient_totals[key] = {
                    "ingredient": ing.name,
                    "unit": ing.unit or "pz",
                    "quantity": 0.0,
                }
            ingredient_totals[key]["quantity"] += m.quantity_per_unit * pred_qty

    items = [
        {
            "ingredient": v["ingredient"],
            "quantity": round(v["quantity"], 2),
            "unit": v["unit"],
        }
        for v in ingredient_totals.values()
        if v["quantity"] > 0
    ]

    # Fallback: if no ingredient mappings, estimate from covers
    if not items:
        items = [{
            "ingredient": "Ingredienti (nessuna mappatura configurata)",
            "quantity": fc.expected_covers,
            "unit": "coperti",
            "note": "Vai su /setup per configurare prodotti e ingredienti",
        }]

    # Persist the order
    po = PurchaseOrder(
        restaurant_id=restaurant_id,
        for_date=target,
        items=items,
        status="draft",
    )
    db.add(po)
    db.commit()

    return {
        "id": str(po.id),
        "for_date": str(target),
        "expected_covers": fc.expected_covers,
        "items": items,
        "status": "draft",
    }


def get_staff_plan(db: Session, restaurant_id: uuid.UUID) -> dict:
    """Generate a shift staffing plan based on forecast covers."""
    today = date.today()
    next7 = [today + timedelta(days=i) for i in range(1, 8)]

    forecasts = db.query(Forecast).filter(
        Forecast.restaurant_id == restaurant_id,
        Forecast.date.in_(next7),
    ).all()

    # Avg covers from historical data (baseline)
    all_fc = db.query(Forecast).filter(Forecast.restaurant_id == restaurant_id).all()
    avg_covers = sum(f.expected_covers for f in all_fc) / len(all_fc) if all_fc else 30

    # Simple staffing formula:
    # 1 waiter per 15 covers, min 2, max 10
    # Kitchen: 1 chef per 20 covers, min 1, max 5
    days = []
    for fc in sorted(forecasts, key=lambda x: x.date):
        covers = fc.expected_covers
        waiters = min(10, max(2, round(covers / 15)))
        kitchen = min(5, max(1, round(covers / 20)))
        load = "alta" if covers > avg_covers * 1.3 else "normale" if covers > avg_covers * 0.7 else "bassa"

        days.append({
            "date": str(fc.date),
            "expected_covers": covers,
            "load": load,
            "shifts": {
                "lunch": {
                    "waiters": max(1, waiters - 1),
                    "kitchen": max(1, kitchen - 1),
                    "hours": "11:30–15:30",
                },
                "dinner": {
                    "waiters": waiters,
                    "kitchen": kitchen,
                    "hours": "18:30–23:00",
                },
            },
        })

    if not days:
        return {"message": "Genera prima una previsione per i prossimi 7 giorni.", "days": []}

    return {"days": days, "avg_covers_baseline": round(avg_covers)}


def list_purchase_orders(db: Session, restaurant_id: uuid.UUID) -> list[dict]:
    orders = db.query(PurchaseOrder).filter(
        PurchaseOrder.restaurant_id == restaurant_id,
    ).order_by(PurchaseOrder.created_at.desc()).limit(10).all()
    return [
        {
            "id": str(o.id),
            "for_date": str(o.for_date),
            "status": o.status,
            "item_count": len(o.items),
            "items": o.items,
            "created_at": str(o.created_at),
        }
        for o in orders
    ]
