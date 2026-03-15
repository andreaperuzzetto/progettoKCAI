"""Review analysis module.

Stateless: receives review texts, returns sentiment and topics.
Does not access the database or persist any state.

Uses keyword-based heuristics for sentiment classification
and topic extraction. Can be replaced with an LLM later.
"""

POSITIVE_WORDS = {
    "great", "excellent", "amazing", "fantastic", "wonderful", "good",
    "delicious", "friendly", "love", "loved", "best", "perfect",
    "fresh", "tasty", "recommended", "outstanding", "superb",
}

NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "horrible", "worst", "disgusting",
    "cold", "burnt", "raw", "slow", "rude", "dirty", "stale",
    "overpriced", "disappointing", "undercooked", "overcooked",
    "long", "wait", "waiting", "complained", "complaint",
}

COMPLAINT_TOPICS = {
    "slow service": ["slow service", "slow waiter", "waited too long", "long wait", "waiting time", "took forever"],
    "burnt food": ["burnt", "burned", "overcooked", "charred"],
    "cold food": ["cold food", "cold pizza", "cold pasta", "not warm", "lukewarm"],
    "long waiting time": ["long wait", "waiting time", "waited forever", "took forever", "too long to arrive"],
    "rude staff": ["rude", "unfriendly", "impolite", "disrespectful"],
    "dirty environment": ["dirty", "unclean", "filthy", "hygiene"],
    "overpriced": ["overpriced", "too expensive", "not worth the price", "expensive"],
    "raw food": ["raw", "undercooked", "not cooked"],
    "small portions": ["small portion", "tiny portion", "not enough food"],
}


def classify_sentiment(text: str) -> str:
    """Classify a review as positive, neutral, or negative."""
    words = set(text.lower().split())
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)

    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def extract_topics(text: str) -> list[str]:
    """Extract complaint topics found in a review."""
    lower = text.lower()
    found = []
    for topic, keywords in COMPLAINT_TOPICS.items():
        if any(kw in lower for kw in keywords):
            found.append(topic)
    return found


def analyze_reviews(reviews: list[dict]) -> list[dict]:
    """Analyze a batch of reviews.

    Args:
        reviews: list of {"review_text": str, ...}

    Returns:
        list of {"review_text": str, "sentiment": str, "topics": list[str]}
    """
    results = []
    for review in reviews:
        text = review["review_text"]
        results.append({
            "review_text": text,
            "sentiment": classify_sentiment(text),
            "topics": extract_topics(text),
        })
    return results


def summarize_topics(analyzed: list[dict]) -> dict[str, int]:
    """Count how often each complaint topic appears across all reviews."""
    counts: dict[str, int] = {}
    for item in analyzed:
        for topic in item["topics"]:
            counts[topic] = counts.get(topic, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
