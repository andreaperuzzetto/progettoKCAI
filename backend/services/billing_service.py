import uuid
from datetime import datetime, timedelta, timezone

import stripe
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.models import User


def create_checkout_session(user_id: uuid.UUID, user_email: str) -> str:
    """Create a Stripe checkout session and return the URL."""
    stripe.api_key = settings.stripe_secret_key
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
        customer_email=user_email,
        client_reference_id=str(user_id),
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
        user_id = session_obj.get("client_reference_id")
        if user_id:
            _activate_user(uuid.UUID(user_id), db)

    elif event["type"] in ("customer.subscription.deleted", "customer.subscription.paused"):
        customer_id = event["data"]["object"].get("customer")
        if customer_id:
            _deactivate_by_stripe_customer(customer_id, db)


def _activate_user(user_id: uuid.UUID, db: Session) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.subscription_status = "active"
        db.commit()


def _deactivate_by_stripe_customer(customer_id: str, db: Session) -> None:
    # In a full implementation, store stripe_customer_id on User.
    # For MVP, skip – handle manually if needed.
    pass
