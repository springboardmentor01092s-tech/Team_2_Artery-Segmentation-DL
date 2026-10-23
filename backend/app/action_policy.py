"""Role maximums plus separately granted operational actions.

An allowed action never bypasses resource ownership or case assignment.
Dataset/train/deploy permissions stay off until their scoped services exist.
"""
from sqlalchemy import select
from .models import ActionGrant

DEFAULT_ACTIONS = {
    "viewer": {"case:read_assigned"},
    "researcher": {"case:read_assigned", "case:create", "case:upload", "analysis:run", "analysis:export", "model:read"},
    "technician": {"case:read_assigned", "case:create", "case:upload"},
    "doctor": {"case:read_assigned", "case:create", "case:upload", "analysis:run", "analysis:export", "clinical_review:create"},
    "clinician": {"case:read_assigned", "case:create", "case:upload", "analysis:run", "analysis:export", "clinical_review:create"},
    "ml_engineer": {"model:read"},
    "admin": {"case:read_assigned", "case:create", "case:upload", "analysis:run", "analysis:export", "clinical_review:create", "model:read", "users:manage", "model:activate_research"},
}
CONDITIONAL_ACTIONS = {
    "admin": {"case:create", "case:upload", "analysis:run", "analysis:export"},
    "technician": {"analysis:run"},
}


def allowed_action(user, permission, db):
    if user.status != "active":
        return False
    if permission in DEFAULT_ACTIONS.get(user.role, set()):
        return True
    if permission not in CONDITIONAL_ACTIONS.get(user.role, set()):
        return False
    return bool(db.scalar(select(ActionGrant).where(ActionGrant.user_id == user.id,
                                                    ActionGrant.permission == permission,
                                                    ActionGrant.enabled.is_(True))))


def effective_actions(user, db):
    names = set(DEFAULT_ACTIONS.get(user.role, set())) | set(CONDITIONAL_ACTIONS.get(user.role, set()))
    return sorted(name for name in names if allowed_action(user, name, db))
