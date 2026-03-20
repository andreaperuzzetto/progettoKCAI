import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

import stripe
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.models import User

Plan = Literal["starter", "pro", "premium"]

PLAN_PRICES: dict[Plan, str] = {}  # populated lazily from settings


def _price_for_plan(plan: Plan) -> str:
    mapping = {
        "starter": settings.stripe_price_id_starter or settings.stripe_price_id,
        "pro": settings.stripe_price_id_pro,
        "premium": settings.stripe_price_id_premium,
    }
    price_id = mapping.get(plan, "")
    if not price_id:
        raise ValueError(f"Stripe price ID non configurato per il piano '{plan}'. Imposta STRIPE_PRICE_ID_{plan.upper()} nel .env")
    return price_id


def create_checkout_session(user_id: uuid.UUID, user_email: str, plan: Plan = "starter") -> str:
    """Create a Stripe checkout session for the chosen plan and return the URL."""
    if not settings.stripe_secret_key:
        raise ValueError("Stripe non configurato. Imposta STRIPE_SECRET_KEY nel .env")
    stripe.api_key = settings.stripe_secret_key
    price_id = _price_for_plan(plan)
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        customer_email=user_email,
        client_reference_id=f"{user_id}:{plan}",  # encode plan in reference
        success_url="http://localhost:3000/?checkout=success",
        cancel_url="http://localhost:3000/billing?checkout=cancelled",
    )
    return session.url


def handle_webhook(payload: bytes, sig_header: str, db: Session) -> None:
    """Process Stripe webhook events to update subscription status."""
    stripe.api_key = settings.stripe_secret_key
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except stripe.error.SignatureVerificationError:
        raise ValueError("Invalid Stripe signature")

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        ref = session_obj.get("client_reference_id", "")
        if ":" in ref:
            user_id_str, plan = ref.split(":", 1)
        else:
            user_id_str, plan = ref, "starter"
        if user_id_str:
            _activate_user(uuid.UUID(user_id_str), plan, db)

    elif event["type"] in ("customer.subscription.deleted", "customer.subscription.paused"):
        customer_id = event["data"]["object"].get("customer")
        if customer_id:
            _deactivate_by_stripe_customer(customer_id, db)


def _activate_user(user_id: uuid.UUID, plan: str, db: Session) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.subscription_status = "active"
        user.plan = plan if plan in ("starter", "pro", "premium") else "starter"
        db.commit()


def _deactivate_by_stripe_customer(customer_id: str, db: Session) -> None:
    # Full impl: store stripe_customer_id on User and look up here.
    pass
