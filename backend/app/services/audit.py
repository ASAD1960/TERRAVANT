from sqlalchemy.orm import Session

from app.models import AuditLog


def audit(db: Session, user_id: str | None, action: str, resource: str | None = None, details: dict | None = None) -> None:
    db.add(AuditLog(user_id=user_id, action=action, resource=resource, details=details))
    db.flush()
