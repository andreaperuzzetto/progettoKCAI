"""
Correlation Engine V2 — LLM-based causal analysis.

Combines sales trends + review issues + forecast into a single LLM prompt.
Returns [{cause, confidence, suggestion, impact_level}].

Falls back gracefully when OpenAI API key is not set.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

logger = logging.getLogger(__name__)


def _build_context(
    sales: list[dict[str, Any]],
    forecast_tomorrow: dict[str, Any],
    issues: list[dict[str, Any]],
    avg_covers: float,
) -> str:
    """Summarize data into a compact text block for the prompt."""
    today = date.today()

    # Sales: last 7 days total and top products
    last_7 = today - timedelta(days=7)
    prev_7 = today - timedelta(days=14)
    recent_sales: dict[str, int] = defaultdict(int)
    older_sales: dict[str, int] = defaultdict(int)
    for row in sales:
        if row["date"] >= last_7:
            recent_sales[row["product_name"]] += row["quantity"]
        elif row["date"] >= prev_7:
            older_sales[row["product_name"]] += row["quantity"]

    total_recent = sum(recent_sales.values())
    total_older = sum(older_sales.values())
    trend_pct = round((total_recent - total_older) / total_older * 100) if total_older > 0 else 0
    top_products = sorted(recent_sales.items(), key=lambda x: x[1], reverse=True)[:3]
    products_str = ", ".join(f"{n}: {q}" for n, q in top_products) or "n/d"

    tomorrow_covers = forecast_tomorrow.get("expected_covers", 0)
    cover_vs_avg = round((tomorrow_covers / avg_covers - 1) * 100) if avg_covers > 0 else 0
    issues_str = (
        "; ".join(f"{i['name']} (freq {i.get('frequency', 1)})" for i in issues[:5])
        if issues else "nessun problema segnalato"
    )

    return f"""DATI RISTORANTE (ultimi 7 giorni):
- Tendenza vendite: {'+' if trend_pct >= 0 else ''}{trend_pct}% rispetto ai 7 giorni precedenti
- Prodotti più venduti: {products_str}
- Coperti previsti domani: {tomorrow_covers} ({'+' if cover_vs_avg >= 0 else ''}{cover_vs_avg}% vs media)
- Problemi nelle recensioni: {issues_str}"""


SYSTEM_PROMPT = """Sei un consulente operativo per ristoranti. Analizza i dati forniti e individua le correlazioni causali tra problemi operativi e dati di vendita/previsione.

Rispondi SOLO con un array JSON valido. Ogni elemento deve avere:
- cause: causa probabile (stringa breve, max 10 parole)
- confidence: numero da 0 a 1 (es. 0.8)
- suggestion: azione concreta e specifica (1-2 frasi)
- impact_level: "high" | "medium" | "low"

Esempio formato:
[
  {"cause": "understaffing nelle ore di punta", "confidence": 0.85, "suggestion": "Aggiungi 1-2 camerieri nelle fasce 19-22. Priorità alta per domani.", "impact_level": "high"}
]

Regole:
- massimo 5 correlazioni
- solo correlazioni con confidence >= 0.6
- suggerimenti concreti e azionabili, non generici
- se i dati sono insufficienti, restituisci []"""


def run_llm_correlation(
    sales: list[dict[str, Any]],
    forecast_tomorrow: dict[str, Any],
    issues: list[dict[str, Any]],
    avg_covers: float,
    api_key: str = "",
) -> list[dict[str, Any]]:
    """
    Call GPT-4o-mini to find causal correlations.
    Returns [] if no key or insufficient data.
    """
    if not api_key:
        return _rule_based_fallback(issues, forecast_tomorrow, avg_covers)

    if not sales and not issues:
        return []

    context = _build_context(sales, forecast_tomorrow, issues, avg_covers)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        raw = response.choices[0].message.content
        parsed = json.loads(raw)
        correlations = parsed if isinstance(parsed, list) else parsed.get("correlations", [])
        return _postprocess(correlations)

    except Exception as e:
        logger.error("Correlation LLM call failed: %s", e)
        return _rule_based_fallback(issues, forecast_tomorrow, avg_covers)


def _postprocess(correlations: list[dict]) -> list[dict]:
    """Filter low confidence, cap at 5, sort by impact."""
    order = {"high": 0, "medium": 1, "low": 2}
    filtered = [c for c in correlations if float(c.get("confidence", 0)) >= 0.6]
    sorted_ = sorted(filtered, key=lambda x: order.get(x.get("impact_level", "low"), 2))
    return sorted_[:5]


def _rule_based_fallback(
    issues: list[dict], forecast_tomorrow: dict, avg_covers: float
) -> list[dict]:
    """Minimal rule-based fallback when LLM is unavailable."""
    results = []
    covers = forecast_tomorrow.get("expected_covers", 0)
    ratio = covers / avg_covers if avg_covers > 0 else 1.0

    issue_names = [i.get("name", "").lower() for i in issues]

    if any("lento" in n or "attesa" in n for n in issue_names) and ratio > 1.2:
        results.append({
            "cause": "personale insufficiente in ore di punta",
            "confidence": 0.8,
            "suggestion": f"Con {covers} coperti previsti e problemi di lentezza segnalati, considera personale extra nelle fasce 19-22.",
            "impact_level": "high",
        })
    if any("freddo" in n or "temperatura" in n for n in issue_names):
        results.append({
            "cause": "tempi di preparazione eccessivi",
            "confidence": 0.75,
            "suggestion": "I piatti freddi indicano un backlog in cucina. Riduci la complessità del menu nei momenti di alta domanda.",
            "impact_level": "high",
        })
    if any("pulizia" in n or "sporco" in n for n in issue_names):
        results.append({
            "cause": "procedure di pulizia insufficienti",
            "confidence": 0.9,
            "suggestion": "Implementa checklist pulizia pre-apertura. Assegna responsabile specifico.",
            "impact_level": "high",
        })

    return results
