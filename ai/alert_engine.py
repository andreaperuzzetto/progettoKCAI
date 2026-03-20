"""
Alert detection engine.

Detects 5 types of conditions and returns alert dicts.
Called by alert_service.py to persist and notify.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any


AlertDict = dict[str, Any]


def detect_high_demand(
    forecast: list[dict[str, Any]],
    avg_historical_covers: float,
    threshold: float = 0.30,
) -> AlertDict | None:
    """Alert when tomorrow's covers exceed historical average by threshold%."""
    if not forecast or avg_historical_covers <= 0:
        return None
    tomorrow = forecast[0]
    expected = tomorrow.get("expected_covers", 0)
    ratio = expected / avg_historical_covers
    if ratio >= 1 + threshold:
        pct = round((ratio - 1) * 100)
        return {
            "type": "high_demand",
            "severity": "high" if pct >= 50 else "medium",
            "message": f"Domani domanda alta: attesi {expected} coperti (+{pct}% rispetto alla media). Aumenta preparazione e personale.",
        }
    return None


def detect_negative_review_spike(
    historical_sentiment: list[dict[str, Any]],  # [{date, negative_pct}, …]
    threshold: float = 15.0,                      # absolute % increase
) -> AlertDict | None:
    """Alert when negative sentiment has risen sharply in recent analysis."""
    if len(historical_sentiment) < 2:
        return None
    latest = historical_sentiment[-1].get("negative_pct", 0)
    previous = historical_sentiment[-2].get("negative_pct", 0)
    delta = latest - previous
    if delta >= threshold:
        return {
            "type": "negative_spike",
            "severity": "high",
            "message": f"Aumento recensioni negative: +{round(delta)}% rispetto all'ultima analisi. Controlla le ultime recensioni.",
        }
    return None


def detect_sales_anomaly(
    historical_sales: list[dict[str, Any]],
    threshold: float = 0.30,
) -> AlertDict | None:
    """Alert when total sales in last 3 days dropped >threshold% vs previous 7 days."""
    if not historical_sales:
        return None
    today = date.today()
    last_3 = today - timedelta(days=3)
    prev_7 = today - timedelta(days=10)

    recent = sum(r["quantity"] for r in historical_sales if r["date"] >= last_3)
    older = sum(r["quantity"] for r in historical_sales if prev_7 <= r["date"] < last_3)

    if older <= 0:
        return None
    # Normalize to daily avg
    recent_daily = recent / 3
    older_daily = older / 7
    drop = (older_daily - recent_daily) / older_daily

    if drop >= threshold:
        pct = round(drop * 100)
        return {
            "type": "sales_drop",
            "severity": "high" if pct >= 50 else "medium",
            "message": f"Calo vendite: -{pct}% nelle ultime 3 giornate rispetto alla settimana precedente. Verifica la situazione.",
        }
    return None


def detect_low_sentiment(
    analysis: Any | None,  # AnalysisResult ORM object or dict
    threshold: float = 40.0,
) -> AlertDict | None:
    """Alert when positive sentiment falls below threshold."""
    if analysis is None:
        return None
    pos = (
        analysis.get("sentiment_positive")
        if isinstance(analysis, dict)
        else getattr(analysis, "sentiment_positive", None)
    )
    if pos is None:
        return None
    if pos < threshold:
        return {
            "type": "low_sentiment",
            "severity": "high" if pos < 25 else "medium",
            "message": f"Sentiment basso: solo {round(pos)}% di recensioni positive. Intervieni immediatamente sulle aree problematiche.",
        }
    return None


def detect_issue_increase(
    issues_now: list[dict[str, Any]],
    issues_prev: list[dict[str, Any]],
    threshold: int = 2,
) -> AlertDict | None:
    """Alert when an issue's frequency increases significantly."""
    if not issues_now or not issues_prev:
        return None

    prev_map = {i["name"]: i.get("frequency", 0) for i in issues_prev}
    alerts = []
    for issue in issues_now:
        name = issue["name"]
        freq_now = issue.get("frequency", 0)
        freq_prev = prev_map.get(name, 0)
        delta = freq_now - freq_prev
        if delta >= threshold:
            alerts.append(f"'{name}' (+{delta})")

    if alerts:
        return {
            "type": "issue_increase",
            "severity": "medium",
            "message": f"Problemi in aumento nelle recensioni: {', '.join(alerts[:3])}. Intervieni prima che si diffondano.",
        }
    return None


def run_all_detections(
    forecast: list[dict[str, Any]],
    historical_sales: list[dict[str, Any]],
    avg_historical_covers: float,
    analysis_now: Any | None,
    analysis_prev: Any | None,
) -> list[AlertDict]:
    """Run all detectors and return non-None results."""
    detectors_results = [
        detect_high_demand(forecast, avg_historical_covers),
        detect_sales_anomaly(historical_sales),
        detect_low_sentiment(analysis_now),
    ]

    # Issue increase (compare last two analyses)
    if analysis_now and analysis_prev:
        issues_now = (
            analysis_now.get("issues") if isinstance(analysis_now, dict) else getattr(analysis_now, "issues", [])
        ) or []
        issues_prev = (
            analysis_prev.get("issues") if isinstance(analysis_prev, dict) else getattr(analysis_prev, "issues", [])
        ) or []
        detectors_results.append(detect_issue_increase(issues_now, issues_prev))

    return [a for a in detectors_results if a is not None]
