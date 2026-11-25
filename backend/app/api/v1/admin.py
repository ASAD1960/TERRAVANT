from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.database import get_db
from app.ml.registry import registry
from app.models import AuditLog, ModelVersion, Role, User, UserSession
from app.schemas.user import UserOut
from app.services.audit import audit

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_roles("admin")
ops = require_roles("admin", "operator")


class StatusIn(BaseModel):
    status: str = Field(pattern="^(active|suspended)$")


class RolesIn(BaseModel):
    roles: list[str] = Field(min_length=1)


class DeployIn(BaseModel):
    deployment_status: str = Field(pattern="^(staged|active|retired)$")


@router.get("/users", response_model=list[UserOut])
def users(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), _: User = Depends(admin_only), db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)).all()


@router.patch("/users/{uid}/status", response_model=UserOut)
def set_status(uid: str, body: StatusIn, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    user = db.get(User, uid)
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == admin.id:
        raise HTTPException(400, "You cannot change your own status")
    user.status = body.status

    if body.status == "suspended":
        db.execute(
            update(UserSession)
            .where(
                UserSession.user_id == user.id,
                UserSession.revoked_at.is_(None),
            )
            .values(
                revoked_at=datetime.now(timezone.utc),
                revocation_reason="account_suspended",
            )
            .execution_options(synchronize_session=False)
        )

    audit(db, admin.id, "admin.user_status", "users", {"target": uid, "status": body.status})
    db.commit()
    return user


@router.put("/users/{uid}/roles", response_model=UserOut)
def set_roles(uid: str, body: RolesIn, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    user = db.get(User, uid)
    if not user:
        raise HTTPException(404, "User not found")
    roles = list(db.scalars(select(Role).where(Role.name.in_(body.roles))))
    if len(roles) != len(set(body.roles)):
        raise HTTPException(422, "Unknown role in request")
    user.roles = roles
    audit(db, admin.id, "admin.user_roles", "users", {"target": uid, "roles": body.roles})
    db.commit()
    return user


@router.get("/models")
def models(_: User = Depends(ops), db: Session = Depends(get_db)):
    rows = db.scalars(select(ModelVersion).order_by(ModelVersion.created_at.desc())).all()
    return {
        "artifacts_present": registry.available(),
        "versions": [{"id": m.id, "model_name": m.model_name, "version": m.version, "model_type": m.model_type, "metrics": m.metrics,
                      "data_source": m.data_source, "deployment_status": m.deployment_status, "created_at": m.created_at} for m in rows],
    }


@router.patch("/models/{mid}")
def set_model_status(mid: str, body: DeployIn, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    m = db.get(ModelVersion, mid)
    if not m:
        raise HTTPException(404, "Model version not found")
    m.deployment_status = body.deployment_status
    audit(db, admin.id, "admin.model_status", "model_versions", {"id": mid, "status": body.deployment_status})
    db.commit()
    return {"id": m.id, "deployment_status": m.deployment_status}


@router.get("/audit-logs")
def audit_logs(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), action: str | None = None,
               _: User = Depends(admin_only), db: Session = Depends(get_db)):
    q = select(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    if action:
        q = q.where(AuditLog.action == action)
    return [{"id": a.id, "user_id": a.user_id, "action": a.action, "resource": a.resource, "details": a.details, "created_at": a.created_at}
            for a in db.scalars(q)]


@router.get("/overview")
def overview(_: User = Depends(ops), db: Session = Depends(get_db)):
    return {"users": db.scalar(select(func.count(User.id))) or 0, "audit_events": db.scalar(select(func.count(AuditLog.id))) or 0,
            "models": registry.available()}
