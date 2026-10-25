from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, auth
from ..database import get_db

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


@router.get("")
def list_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrators only")
    rows = (
        db.query(models.AuditLog)
        .order_by(models.AuditLog.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "user": r.user_name,
            "role": r.role,
            "action": r.action,
            "detail": r.detail,
            "time": r.created_at,
        }
        for r in rows
    ]