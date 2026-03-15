from sqlalchemy.orm import Session

from backend.db.models import Sales, Reviews
from ai.review_analysis_model import analyze_reviews, summarize_topics
from ai.correlation_model import correlate


def run_correlation(restaurant_id, db: Session) -> dict:
    # Load reviews
    review_rows = db.query(Reviews).filter(Reviews.restaurant_id == restaurant_id).all()
    reviews = [{"review_text": r.review_text} for r in review_rows]

    if not reviews:
        return {"hypotheses": []}

    # Run review analysis to get topics
    analyzed = analyze_reviews(reviews)
    topics = summarize_topics(analyzed)

    # Collect dates of negative reviews
    complaint_dates = [
        r.date for r in review_rows
        if r.sentiment == "negative"
    ]

    # Load sales data
    sales_rows = db.query(Sales).filter(Sales.restaurant_id == restaurant_id).all()
    sales = [
        {"date": s.date, "product": s.product, "quantity": s.quantity}
        for s in sales_rows
    ]

    hypotheses = correlate(topics, sales, complaint_dates)
    return {"hypotheses": hypotheses}
