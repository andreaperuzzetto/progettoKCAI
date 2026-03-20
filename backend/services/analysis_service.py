import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ai.llm_analysis import analyze
from backend.db.models import AnalysisResult, Reviews


def run_analysis(restaurant_id: uuid.UUID, period: str, db: Session) -> dict:
    """Run LLM analysis on restaurant reviews and persist the result."""
    query = db.query(Reviews).filter(Reviews.restaurant_id == restaurant_id)

    if period == "last_30_days":
        cutoff = datetime.utcnow().date() - timedelta(days=30)
        query = query.filter(Reviews.date >= cutoff)

    rows = query.all()
    reviews = [{"review_text": r.review_text} for r in rows]

    result = analyze(reviews)

    record = AnalysisResult(
        restaurant_id=restaurant_id,
        period=period,
        sentiment_positive=result["sentiment"]["positive_percentage"],
        sentiment_negative=result["sentiment"]["negative_percentage"],
        issues=result["issues"],
        strengths=result["strengths"],
        suggestions=result["suggestions"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _serialize(record)


def get_latest(restaurant_id: uuid.UUID, db: Session) -> dict | None:
    record = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.restaurant_id == restaurant_id)
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )
    if not record:
        return None
    return _serialize(record)


def _serialize(record: AnalysisResult) -> dict:
    return {
        "id": str(record.id),
        "restaurant_id": str(record.restaurant_id),
        "period": record.period,
        "sentiment": {
            "positive_percentage": record.sentiment_positive,
            "negative_percentage": record.sentiment_negative,
        },
        "issues": record.issues,
        "strengths": record.strengths,
        "suggestions": record.suggestions,
        "created_at": record.created_at.isoformat(),
    }
