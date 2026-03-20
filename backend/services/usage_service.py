import uuid
from sqlalchemy.orm import Session
from backend.db.models import UsageLog


def log_action(user_id: uuid.UUID, action: str, db: Session) -> None:
    db.add(UsageLog(user_id=user_id, action=action))
    db.commit()
