"""
Proactive AI Insights Engine.

Detects events from sales + reviews + forecast data, then classifies and
ranks insights by confidence × impact. Returns top 3 only.

Insight types:
  predictive  — "domani rischio overload cucina"
  diagnostic  — "calo vendite causato da servizio lento"
  prescriptive — "aggiungi 1 cameriere fascia 19-22"
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _rule_based_insights(
    sales_last7: list[dict],
    sales_prev7: list[dict],
    forecast_tomorrow: dict | None,
    issues: list[dict],
    avg_covers: float,
) -> list[dict]:
    insights = []

    last7_qty = sum(s.get("quantity", 0) for s in sales_last7)
    prev7_qty = sum(s.get("quantity", 0) for s in sales_prev7)

    # Diagnostic: significant sales drop
    if prev7_qty > 0 and last7_qty < prev7_qty * 0.70:
        drop_pct = round((1 - last7_qty / prev7_qty) * 100)
        top_issue = issues[0]["name"] if issues else "qualità del servizio"
        insights.append({
            "type": "diagnostic",
            "message": f"Le vendite sono calate del {drop_pct}% rispetto alla settimana precedente. "
                       f"Possibile causa: problemi con '{top_issue}' evidenziati nelle recensioni.",
            "confidence": 0.75,
            "impact": 0.85,
        })

    # Predictive: high demand tomorrow
    if forecast_tomorrow and avg_covers > 0:
        tomorrow_covers = forecast_tomorrow.get("expected_covers", 0)
        if tomorrow_covers > avg_covers * 1.30:
            delta_pct = round((tomorrow_covers / avg_covers - 1) * 100)
            insights.append({
                "type": "predictive",
                "message": f"Domani è previsto un afflusso di {tomorrow_covers} coperti (+{delta_pct}% rispetto alla media). "
                           f"Rischio di overload operativo.",
                "confidence": 0.80,
                "impact": 0.90,
            })

    # Prescriptive: recurring service issues
    service_issues = [i for i in issues if any(k in i["name"].lower() for k in ["servizio", "attesa", "lento", "cameriere"])]
    if service_issues:
        freq = service_issues[0].get("frequency", 1)
        insights.append({
            "type": "prescriptive",
            "message": f"Il problema '{service_issues[0]['name']}' compare {freq} volte nelle recensioni recenti. "
                       f"Valuta di aggiungere personale nelle fasce di punta (19–22).",
            "confidence": 0.70,
            "impact": 0.75,
        })

    # Prescriptive: cold food / kitchen issues
    kitchen_issues = [i for i in issues if any(k in i["name"].lower() for k in ["freddo", "cucina", "cottura", "qualità"])]
    if kitchen_issues:
        insights.append({
            "type": "prescriptive",
            "message": f"Problemi di cucina rilevati ('{kitchen_issues[0]['name']}'). "
                       f"Riduci il backlog: limita le prenotazioni o aggiungi un turno in cucina.",
            "confidence": 0.65,
            "impact": 0.70,
        })

    return insights


def _llm_insights(
    sales_last7: list[dict],
    sales_prev7: list[dict],
    forecast_tomorrow: dict | None,
    issues: list[dict],
    avg_covers: float,
    api_key: str,
) -> list[dict]:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        sales_delta = ""
        last7_qty = sum(s.get("quantity", 0) for s in sales_last7)
        prev7_qty = sum(s.get("quantity", 0) for s in sales_prev7)
        if prev7_qty > 0:
            delta = round((last7_qty / prev7_qty - 1) * 100)
            sales_delta = f"{'+' if delta >= 0 else ''}{delta}% vs settimana precedente"

        prompt = f"""Sei un consulente operativo per ristoranti. Analizza questi dati e genera insight azionabili.

Dati:
- Vendite ultimi 7 giorni: {last7_qty} unità totali ({sales_delta})
- Coperti medi: {round(avg_covers)}
- Previsione domani: {forecast_tomorrow.get('expected_covers', 'N/D') if forecast_tomorrow else 'N/D'} coperti
- Problemi dalle recensioni: {json.dumps(issues[:3], ensure_ascii=False)}

Genera esattamente 3 insight. Ogni insight deve:
- essere concreto e specifico (no genericità)
- indicare una causa chiara
- proporre un'azione operativa precisa

Rispondi SOLO con JSON:
[
  {{
    "type": "predictive|diagnostic|prescriptive",
    "message": "testo italiano chiaro e breve (max 2 righe)",
    "confidence": 0.0-1.0,
    "impact": 0.0-1.0
  }}
]"""

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        raw = resp.choices[0].message.content or "[]"
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        # sometimes wrapped in a key
        for v in parsed.values():
            if isinstance(v, list):
                return v
        return []
    except Exception as e:
        logger.warning("LLM insights failed: %s — using rule-based fallback", e)
        return []


def run_insights(
    sales_last7: list[dict],
    sales_prev7: list[dict],
    forecast_tomorrow: dict | None,
    issues: list[dict],
    avg_covers: float,
    api_key: str = "",
) -> list[dict]:
    """Return top 3 insights ranked by confidence × impact."""
    if api_key:
        insights = _llm_insights(sales_last7, sales_prev7, forecast_tomorrow, issues, avg_covers, api_key)
    else:
        insights = []

    if not insights:
        insights = _rule_based_insights(sales_last7, sales_prev7, forecast_tomorrow, issues, avg_covers)

    # Rank and cap at 3
    ranked = sorted(insights, key=lambda x: x.get("confidence", 0) * x.get("impact", 0), reverse=True)
    return ranked[:3]
