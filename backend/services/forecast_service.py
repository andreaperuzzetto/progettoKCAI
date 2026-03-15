from datetime import date

from sqlalchemy.orm import Session

from backend.db.models import Sales, Forecast
from ai.forecasting_model import forecast_demand


def load_sales(restaurant_id, db: Session) -> list[dict]:
    rows = db.query(Sales).filter(Sales.restaurant_id == restaurant_id).all()
    return [
        {"date": r.date, "product": r.product, "quantity": r.quantity}
        for r in rows
    ]


def run_forecast(restaurant_id, target_date: date, db: Session) -> dict[str, int]:
    sales = load_sales(restaurant_id, db)
    predictions = forecast_demand(sales, target_date)

    # Store predictions
    for product, qty in predictions.items():
        record = Forecast(
            restaurant_id=restaurant_id,
            date=target_date,
            product=product,
            predicted_quantity=qty,
        )
        db.add(record)
    db.commit()

    return predictions
