from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models import User
from backend.services.billing_service import create_checkout_session, handle_webhook

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    plan: Optional[str] = "starter"


@router.post("/checkout")
def checkout(
    body: CheckoutRequest = CheckoutRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from backend.config import settings
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Billing non configurato. Contatta il supporto.")
    plan = body.plan if body.plan in ("starter", "pro", "premium") else "starter"
    try:
        url = create_checkout_session(current_user.id, current_user.email, plan)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"checkout_url": url}


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        handle_webhook(payload, sig, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}
