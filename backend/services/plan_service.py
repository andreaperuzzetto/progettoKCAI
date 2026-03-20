"""
Plan-based feature gating.

Plans:
  starter  (49€/mese): reviews upload, analysis, basic dashboard
  pro      (99€/mese): + forecast, operational suggestions, alerts
  premium  (199€/mese): + integrations, correlation engine V2, advanced alerts
"""

from backend.db.models import User

PLAN_FEATURES: dict[str, set[str]] = {
    "starter": {"reviews", "analysis", "dashboard"},
    "pro": {"reviews", "analysis", "dashboard", "forecast", "suggestions", "alerts"},
    "premium": {"reviews", "analysis", "dashboard", "forecast", "suggestions", "alerts", "integrations", "correlations_v2"},
}

# Trial users get full access for 7 days
TRIAL_FEATURES = PLAN_FEATURES["premium"]


def has_feature(user: User, feature: str) -> bool:
    if user.subscription_status == "inactive":
        return False
    if user.subscription_status == "trial":
        return feature in TRIAL_FEATURES
    plan = getattr(user, "plan", "starter") or "starter"
    return feature in PLAN_FEATURES.get(plan, PLAN_FEATURES["starter"])


def require_feature(user: User, feature: str) -> None:
    """Raise HTTP 402 / 403 if user's plan doesn't include the feature."""
    from fastapi import HTTPException
    if user.subscription_status == "inactive":
        raise HTTPException(status_code=402, detail="Piano scaduto. Attiva o rinnova il piano.")
    if not has_feature(user, feature):
        plan = getattr(user, "plan", "starter")
        raise HTTPException(
            status_code=403,
            detail=f"La funzione '{feature}' non è disponibile nel piano {plan}. Passa a un piano superiore."
        )
