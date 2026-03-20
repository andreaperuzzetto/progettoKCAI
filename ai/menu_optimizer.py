"""
Menu Optimization Engine.

Classifies products using a 2x2 matrix:
  popularity × margin (or revenue proxy if margin unknown)

Classification:
  high_pop + high_margin  → promote (stars)
  high_pop + low_margin   → optimize_price
  low_pop  + high_margin  → reposition (hidden gems)
  low_pop  + low_margin   → remove
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_THRESHOLDS = {
    "high_popularity": 0.5,   # normalized 0-1
    "high_revenue": 0.5,      # normalized 0-1
}


def _normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    min_v, max_v = min(values), max(values)
    span = max_v - min_v
    if span == 0:
        return [0.5] * len(values)
    return [(v - min_v) / span for v in values]


def analyze_menu(product_metrics: list[dict]) -> list[dict]:
    """
    Input: list of {product_name, total_quantity, total_revenue, trend_7d, popularity_score}
    Output: list of {product, action, reason, priority}
    """
    if not product_metrics:
        return []

    pop_scores = [m.get("popularity_score", 0) for m in product_metrics]
    rev_scores = [float(m.get("total_revenue") or 0) for m in product_metrics]

    norm_pop = _normalize(pop_scores)
    norm_rev = _normalize(rev_scores)

    suggestions = []
    for i, m in enumerate(product_metrics):
        pop = norm_pop[i]
        rev = norm_rev[i]
        trend = m.get("trend_7d", 0)
        name = m["product_name"]

        high_pop = pop >= _THRESHOLDS["high_popularity"]
        high_rev = rev >= _THRESHOLDS["high_revenue"]

        if high_pop and high_rev:
            action = "promote"
            reason = f"Alta popolarità e alto fatturato. {'Tendenza in crescita.' if trend > 5 else 'Considera promozioni e posizionamento in menu.'}"
            priority = "high"
        elif high_pop and not high_rev:
            action = "optimize_price"
            reason = f"Molto richiesto ma genera poco fatturato. Valuta un aumento di prezzo del 10-15%."
            priority = "high"
        elif not high_pop and high_rev:
            action = "reposition"
            reason = f"Alto fatturato ma poco ordinato. Posizionalo meglio nel menu o usalo come speciale del giorno."
            priority = "medium"
        else:
            if trend < -10:
                action = "remove"
                reason = f"Bassa popolarità, basso fatturato e in calo ({round(trend)}%). Valuta la rimozione dal menu."
                priority = "low"
            else:
                action = "monitor"
                reason = f"Bassa performance attuale. Monitora per altri 2 settimane prima di decidere."
                priority = "low"

        suggestions.append({
            "product": name,
            "action": action,
            "reason": reason,
            "priority": priority,
            "popularity_score": round(pop, 2),
            "revenue_score": round(rev, 2),
            "trend_7d": round(trend, 1),
        })

    # Sort: high priority first, then by action importance
    order = {"promote": 0, "optimize_price": 1, "reposition": 2, "remove": 3, "monitor": 4}
    suggestions.sort(key=lambda x: order.get(x["action"], 5))

    return suggestions
