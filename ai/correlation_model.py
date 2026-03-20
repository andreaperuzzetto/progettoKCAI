"""Correlation engine module.

Stateless: receives complaint topics and sales data, returns hypotheses.
Does not access the database or persist any state.

Uses simple heuristics to link complaints with operational anomalies.
"""

from datetime import date
from collections import defaultdict

# Maps complaint topics to plausible operational causes and suggested actions
HYPOTHESIS_RULES: dict[str, dict] = {
    "burnt food": {
        "spike_cause": "oven overload during high-volume periods",
        "default_cause": "kitchen quality control issue",
        "suggested_action": "reduce simultaneous oven orders or add kitchen capacity",
    },
    "cold food": {
        "spike_cause": "too many orders caused delayed serving",
        "default_cause": "food sitting too long before delivery",
        "suggested_action": "improve plating-to-table speed",
    },
    "slow service": {
        "spike_cause": "order volume exceeded staffing capacity",
        "default_cause": "possible understaffing",
        "suggested_action": "add one waiter during peak hours",
    },
    "long waiting time": {
        "spike_cause": "order volume exceeded kitchen capacity",
        "default_cause": "possible understaffing or kitchen bottleneck",
        "suggested_action": "add staff during peak hours",
    },
    "rude staff": {
        "spike_cause": "staff overwhelmed by high order volume",
        "default_cause": "staff training issue",
        "suggested_action": "review staffing levels and training",
    },
    "raw food": {
        "spike_cause": "kitchen rushing due to high demand",
        "default_cause": "kitchen quality control issue",
        "suggested_action": "enforce cooking time standards",
    },
    "small portions": {
        "spike_cause": "kitchen rationing due to supply pressure",
        "default_cause": "portion standard issue",
        "suggested_action": "review portion guidelines",
    },
}

SPIKE_THRESHOLD = 1.5  # 50% above average = spike


def detect_spikes(sales: list[dict]) -> dict[date, bool]:
    """Detect dates where total order volume spiked above average."""
    daily_totals: dict[date, int] = defaultdict(int)
    for row in sales:
        daily_totals[row["date"]] += row["quantity"]

    if not daily_totals:
        return {}

    avg = sum(daily_totals.values()) / len(daily_totals)
    return {d: total > avg * SPIKE_THRESHOLD for d, total in daily_totals.items()}


def correlate(
    topics: dict[str, int],
    sales: list[dict],
    complaint_dates: list[date],
) -> list[dict]:
    """Generate hypotheses linking complaint topics to operational signals.

    Args:
        topics: {"slow service": 3, "burnt food": 2, ...} from review analysis
        sales: list of {"date": date, "product": str, "quantity": int}
        complaint_dates: dates when negative reviews occurred

    Returns:
        list of {"problem", "possible_cause", "suggested_action", "spike_detected"}
    """
    if not topics:
        return []

    spikes = detect_spikes(sales)
    spike_on_complaint = any(spikes.get(d, False) for d in complaint_dates)

    hypotheses = []
    for topic, count in topics.items():
        rule = HYPOTHESIS_RULES.get(topic)
        if not rule:
            hypotheses.append({
                "problem": topic,
                "possible_cause": "requires investigation",
                "suggested_action": f"investigate recurring '{topic}' complaints ({count} occurrences)",
                "spike_detected": spike_on_complaint,
            })
            continue

        cause = rule["spike_cause"] if spike_on_complaint else rule["default_cause"]
        hypotheses.append({
            "problem": topic,
            "possible_cause": cause,
            "suggested_action": rule["suggested_action"],
            "spike_detected": spike_on_complaint,
        })

    return hypotheses
