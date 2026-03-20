"""
Operational suggestions engine.

Combines forecast + product-ingredient mappings to generate:
  - Inventory suggestions (what to buy and how much)
  - Staffing suggestions (based on expected covers)
  - Menu suggestions (fast-growing products)
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def generate_inventory_suggestions(
    forecast: list[dict[str, Any]],   # from forecast_service.get_latest_forecast
    product_ingredient_map: dict[str, list[dict[str, Any]]],  # from products_service
    historical_sales: list[dict[str, Any]],  # last 14 days for trend comparison
) -> list[dict[str, Any]]:
    """
    For each ingredient, compute total needed quantity over forecast horizon.
    Compare to recent average to flag increases (→ buy more).
    """
    if not forecast:
        return []

    # Aggregate predicted quantities per product over next 7 days
    predicted_totals: dict[str, float] = defaultdict(float)
    for day in forecast:
        for product, qty in (day.get("product_predictions") or {}).items():
            predicted_totals[product] += qty

    # Historical average per product (last 14 days, daily avg)
    hist_totals: dict[str, float] = defaultdict(float)
    days_in_history = 14
    for row in historical_sales:
        hist_totals[row["product_name"]] += row["quantity"]
    hist_daily_avg: dict[str, float] = {k: v / days_in_history for k, v in hist_totals.items()}

    # Compute ingredient requirements
    ingredient_needs: dict[str, dict[str, Any]] = {}  # ingredient_name → {...}
    for product, qty_7days in predicted_totals.items():
        ings = product_ingredient_map.get(product, [])
        for ing in ings:
            ing_name = ing["ingredient_name"]
            unit = ing.get("unit", "")
            needed = qty_7days * ing["quantity_per_unit"]

            if ing_name not in ingredient_needs:
                ingredient_needs[ing_name] = {"quantity": 0.0, "unit": unit}
            ingredient_needs[ing_name]["quantity"] += needed

    suggestions = []
    for ing_name, data in sorted(ingredient_needs.items()):
        qty = round(data["quantity"], 2)
        unit = data["unit"] or ""
        suggestions.append({
            "type": "inventory",
            "message": f"Prepara {qty} {unit} di {ing_name} per i prossimi 7 giorni",
            "priority": "high" if qty > 0 else "low",
            "ingredient": ing_name,
            "quantity_needed": qty,
            "unit": unit,
        })

    return suggestions


def generate_staffing_suggestions(
    forecast: list[dict[str, Any]],
    avg_historical_covers: float,
) -> list[dict[str, Any]]:
    """
    Compare tomorrow's expected covers to historical average.
    Flag when significantly higher or lower.
    """
    if not forecast:
        return []

    tomorrow = forecast[0]
    expected = tomorrow["expected_covers"]

    if avg_historical_covers <= 0:
        return []

    ratio = expected / avg_historical_covers
    suggestions = []

    if ratio >= 1.3:
        suggestions.append({
            "type": "staffing",
            "message": f"Domani attesi ~{expected} coperti (+{round((ratio - 1) * 100)}% rispetto alla media). Considera personale extra.",
            "priority": "high",
        })
    elif ratio <= 0.7:
        suggestions.append({
            "type": "staffing",
            "message": f"Domani attesi ~{expected} coperti (-{round((1 - ratio) * 100)}% rispetto alla media). Possibile riduzione staff.",
            "priority": "medium",
        })

    return suggestions


def generate_menu_suggestions(
    forecast: list[dict[str, Any]],
    historical_sales: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Highlight products with growing or declining trend."""
    from collections import defaultdict
    from datetime import timedelta, date

    if not forecast or not historical_sales:
        return []

    today = date.today()
    last_7 = today - timedelta(days=7)
    prev_7 = today - timedelta(days=14)

    recent: dict[str, float] = defaultdict(float)
    older: dict[str, float] = defaultdict(float)
    for row in historical_sales:
        if row["date"] >= last_7:
            recent[row["product_name"]] += row["quantity"]
        elif row["date"] >= prev_7:
            older[row["product_name"]] += row["quantity"]

    suggestions = []
    for product in recent:
        r = recent[product]
        o = older.get(product, r)  # if no older data, no change
        if o == 0:
            continue
        growth = (r - o) / o
        if growth >= 0.3:
            suggestions.append({
                "type": "menu",
                "message": f"'{product}' in crescita +{round(growth * 100)}% rispetto alla settimana scorsa. Assicura disponibilità.",
                "priority": "medium",
                "product": product,
                "growth_pct": round(growth * 100),
            })
        elif growth <= -0.3:
            suggestions.append({
                "type": "menu",
                "message": f"'{product}' in calo -{round(abs(growth) * 100)}% rispetto alla settimana scorsa. Valuta promozione.",
                "priority": "low",
                "product": product,
                "growth_pct": round(growth * 100),
            })

    return sorted(suggestions, key=lambda x: abs(x["growth_pct"]), reverse=True)[:5]


def generate_all_suggestions(
    forecast: list[dict[str, Any]],
    product_ingredient_map: dict[str, list[dict[str, Any]]],
    historical_sales: list[dict[str, Any]],
    avg_historical_covers: float,
) -> list[dict[str, Any]]:
    """Combined: inventory + staffing + menu suggestions, sorted by priority."""
    priority_order = {"high": 0, "medium": 1, "low": 2}

    all_suggestions = (
        generate_inventory_suggestions(forecast, product_ingredient_map, historical_sales)
        + generate_staffing_suggestions(forecast, avg_historical_covers)
        + generate_menu_suggestions(forecast, historical_sales)
    )

    return sorted(all_suggestions, key=lambda s: priority_order.get(s.get("priority", "low"), 2))
