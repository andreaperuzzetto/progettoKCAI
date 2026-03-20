"""LLM-based review analysis pipeline.

Stateless: receives review texts, returns structured analysis.
Uses OpenAI GPT-4o-mini with JSON mode.
"""

import json
import re
from openai import OpenAI

from backend.config import settings

ANALYSIS_PROMPT = """Analizza le seguenti recensioni di un ristorante.
Restituisci SOLO un JSON valido con questa struttura esatta:
{
  "sentiment": {
    "positive_percentage": <number 0-100>,
    "negative_percentage": <number 0-100>
  },
  "issues": [
    { "name": "<string>", "frequency": <number> }
  ],
  "strengths": [
    { "name": "<string>", "frequency": <number> }
  ],
  "suggestions": [
    { "problem": "<string>", "action": "<string concreta e operativa>" }
  ]
}

Limiti:
- massimo 5 issues
- massimo 5 strengths
- suggerimenti concreti e operativi (es. "aggiungi 1 cameriere nelle fasce 20-22")
- le percentuali devono sommare al massimo 100

Recensioni:
"""

MAX_CHARS_PER_CHUNK = 8000  # ~2000 tokens


def preprocess(reviews: list[dict]) -> list[str]:
    """Deduplicate, trim, and filter short reviews."""
    seen = set()
    result = []
    for r in reviews:
        text = (r.get("review_text") or r.get("text") or "").strip()
        if len(text) < 10:
            continue
        if text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def chunk_reviews(texts: list[str]) -> list[list[str]]:
    """Split reviews into chunks that fit within token limits."""
    chunks = []
    current: list[str] = []
    current_len = 0
    for text in texts:
        if current_len + len(text) > MAX_CHARS_PER_CHUNK and current:
            chunks.append(current)
            current = []
            current_len = 0
        current.append(text)
        current_len += len(text)
    if current:
        chunks.append(current)
    return chunks


def call_llm(texts: list[str]) -> dict:
    """Call OpenAI with a batch of review texts. Returns parsed JSON."""
    client = OpenAI(api_key=settings.openai_api_key)
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Sei un analista di ristoranti. Rispondi solo in JSON valido."},
            {"role": "user", "content": ANALYSIS_PROMPT + numbered},
        ],
        temperature=0.2,
    )
    raw = response.choices[0].message.content
    return json.loads(raw)


def merge_results(results: list[dict]) -> dict:
    """Merge analysis results from multiple chunks."""
    if len(results) == 1:
        return results[0]

    # Average sentiment across chunks
    pos = sum(r["sentiment"]["positive_percentage"] for r in results) / len(results)
    neg = sum(r["sentiment"]["negative_percentage"] for r in results) / len(results)

    # Merge and aggregate issues/strengths
    issues_map: dict[str, int] = {}
    strengths_map: dict[str, int] = {}
    suggestions_map: dict[str, str] = {}

    for r in results:
        for item in r.get("issues", []):
            key = item["name"].lower()
            issues_map[key] = issues_map.get(key, 0) + item["frequency"]
        for item in r.get("strengths", []):
            key = item["name"].lower()
            strengths_map[key] = strengths_map.get(key, 0) + item["frequency"]
        for s in r.get("suggestions", []):
            key = s["problem"].lower()
            if key not in suggestions_map:
                suggestions_map[key] = s["action"]

    return {
        "sentiment": {"positive_percentage": round(pos), "negative_percentage": round(neg)},
        "issues": [{"name": k, "frequency": v} for k, v in sorted(issues_map.items(), key=lambda x: -x[1])][:5],
        "strengths": [{"name": k, "frequency": v} for k, v in sorted(strengths_map.items(), key=lambda x: -x[1])][:5],
        "suggestions": [{"problem": k, "action": v} for k, v in suggestions_map.items()][:5],
    }


def postprocess(result: dict) -> dict:
    """Normalize percentages and sort by frequency."""
    sentiment = result.get("sentiment", {})
    pos = max(0, min(100, float(sentiment.get("positive_percentage", 0))))
    neg = max(0, min(100, float(sentiment.get("negative_percentage", 0))))

    issues = sorted(result.get("issues", []), key=lambda x: x.get("frequency", 0), reverse=True)[:5]
    strengths = sorted(result.get("strengths", []), key=lambda x: x.get("frequency", 0), reverse=True)[:5]
    suggestions = result.get("suggestions", [])[:5]

    return {
        "sentiment": {"positive_percentage": round(pos), "negative_percentage": round(neg)},
        "issues": issues,
        "strengths": strengths,
        "suggestions": suggestions,
    }


def analyze(reviews: list[dict]) -> dict:
    """Full pipeline: preprocess → chunk → LLM → merge → postprocess."""
    texts = preprocess(reviews)
    if not texts:
        return {
            "sentiment": {"positive_percentage": 0, "negative_percentage": 0},
            "issues": [],
            "strengths": [],
            "suggestions": [],
        }

    chunks = chunk_reviews(texts)
    results = [call_llm(chunk) for chunk in chunks]
    merged = merge_results(results)
    return postprocess(merged)
