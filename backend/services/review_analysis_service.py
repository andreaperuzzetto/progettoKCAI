from sqlalchemy.orm import Session

from backend.db.models import Reviews
from ai.review_analysis_model import analyze_reviews, summarize_topics


def load_reviews(restaurant_id, db: Session) -> list[dict]:
    rows = db.query(Reviews).filter(Reviews.restaurant_id == restaurant_id).all()
    return [
        {"id": r.id, "review_text": r.review_text}
        for r in rows
    ]


def run_review_analysis(restaurant_id, db: Session) -> dict:
    reviews = load_reviews(restaurant_id, db)
    if not reviews:
        return {"analyzed": 0, "sentiments": {}, "topics": {}}

    results = analyze_reviews(reviews)

    # Update sentiment in DB
    sentiment_map = {r["review_text"]: r["sentiment"] for r in results}
    rows = db.query(Reviews).filter(Reviews.restaurant_id == restaurant_id).all()
    for row in rows:
        if row.review_text in sentiment_map:
            row.sentiment = sentiment_map[row.review_text]
    db.commit()

    # Aggregate sentiments
    sentiments: dict[str, int] = {}
    for r in results:
        sentiments[r["sentiment"]] = sentiments.get(r["sentiment"], 0) + 1

    topics = summarize_topics(results)

    return {
        "analyzed": len(results),
        "sentiments": sentiments,
        "topics": topics,
    }
