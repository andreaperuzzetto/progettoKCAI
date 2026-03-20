"""
Correlation engine: combines review issues with forecast to produce
actionable operational suggestions.

Implementation: rule-based (no ML). Rules are defined as dicts and
evaluated against the current state.
"""

from __future__ import annotations

from typing import Any


# Each rule:
#   issue_keywords: list of strings to match against issue names (lowercase)
#   condition: callable(forecast_tomorrow) -> bool
#   suggestion: string template (can use {covers})
#   priority: high / medium / low

RULES: list[dict[str, Any]] = [
    {
        "issue_keywords": ["servizio lento", "attesa", "slow service", "lentezza"],
        "condition": lambda f: f.get("expected_covers", 0) > 0,
        "suggestion": "Problema rilevato: '{issue}'. Con {covers} coperti previsti domani, considera di aggiungere personale in sala nelle fasce 19-22.",
        "priority": "high",
        "type": "staffing",
    },
    {
        "issue_keywords": ["piatti freddi", "cibo freddo", "temperatura", "cold food"],
        "condition": lambda f: f.get("expected_covers", 0) >= 30,
        "suggestion": "Problema rilevato: '{issue}'. Riduci il backlog in cucina — con {covers} coperti previsti il rischio di ritardi è elevato.",
        "priority": "high",
        "type": "kitchen",
    },
    {
        "issue_keywords": ["porzione piccola", "porzioni piccole", "poco cibo", "quantità insufficiente"],
        "condition": lambda f: True,
        "suggestion": "Problema rilevato: '{issue}'. Valuta se aumentare le porzioni dei piatti più richiesti prima del prossimo servizio.",
        "priority": "medium",
        "type": "menu",
    },
    {
        "issue_keywords": ["prezzo", "caro", "costoso", "prezzi alti"],
        "condition": lambda f: f.get("expected_covers", 0) < 20,
        "suggestion": "Problema rilevato: '{issue}'. Con pochi coperti previsti, potrebbe essere il momento di introdurre un menu fisso a prezzo competitivo.",
        "priority": "medium",
        "type": "menu",
    },
    {
        "issue_keywords": ["pulizia", "sporco", "igiene", "dirty"],
        "condition": lambda f: True,
        "suggestion": "Problema rilevato: '{issue}'. Pianifica una pulizia straordinaria prima dell'apertura.",
        "priority": "high",
        "type": "operations",
    },
    {
        "issue_keywords": ["rumore", "rumoroso", "musica alta", "noise"],
        "condition": lambda f: f.get("expected_covers", 0) >= 40,
        "suggestion": "Problema rilevato: '{issue}'. Con {covers} coperti previsti il locale sarà affollato. Valuta di abbassare la musica nelle prime ore.",
        "priority": "medium",
        "type": "ambiance",
    },
    {
        "issue_keywords": ["parcheggio", "parking", "accesso"],
        "condition": lambda f: f.get("expected_covers", 0) >= 40,
        "suggestion": "Problema rilevato: '{issue}'. Serata intensa prevista ({covers} coperti). Informa i clienti di alternative di parcheggio.",
        "priority": "low",
        "type": "logistics",
    },
]


def _matches_rule(issue_name: str, keywords: list[str]) -> bool:
    issue_lower = issue_name.lower()
    return any(kw in issue_lower for kw in keywords)


def run_correlation(
    issues: list[dict[str, Any]],   # [{name, frequency}, ...]
    forecast_tomorrow: dict[str, Any],  # {expected_covers, product_predictions}
) -> list[dict[str, Any]]:
    """
    Evaluate all rules against current issues + tomorrow's forecast.
    Returns prioritized suggestion list.
    """
    results: list[dict[str, Any]] = []
    covers = forecast_tomorrow.get("expected_covers", 0)

    for issue in issues:
        issue_name = issue.get("name", "")
        for rule in RULES:
            if _matches_rule(issue_name, rule["issue_keywords"]):
                if rule["condition"](forecast_tomorrow):
                    msg = rule["suggestion"].format(issue=issue_name, covers=covers)
                    results.append({
                        "type": rule["type"],
                        "message": msg,
                        "priority": rule["priority"],
                        "source": "correlation",
                        "issue": issue_name,
                    })
                    break  # one rule per issue

    priority_order = {"high": 0, "medium": 1, "low": 2}
    return sorted(results, key=lambda x: priority_order.get(x["priority"], 2))
