from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models import User
from backend.services.billing_service import create_checkout_session, handle_webhook

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout")
def checkout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from backend.config import settings
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Billing not configured")
    url = create_checkout_session(current_user.id, current_user.email)
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
