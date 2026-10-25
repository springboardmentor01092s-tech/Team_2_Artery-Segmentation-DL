from . import models


def log_action(db, user, action, detail=""):
    db.add(
        models.AuditLog(
            user_id=user.id if user else None,
            user_name=user.name if user else None,
            role=user.role if user else None,
            action=action,
            detail=detail,
        )
    )
    db.commit()