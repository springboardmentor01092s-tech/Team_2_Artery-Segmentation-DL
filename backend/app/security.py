import os
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from .models import AuthSession, User

pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")
bearer = HTTPBearer()
SECRET_KEY = os.getenv("JWT_SECRET", "development-only-change-before-deployment")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, stored: str) -> bool:
    return pwd_context.verify(password, stored)


SESSION_HOURS = 8
LOCAL_DEMO_SESSIONS = os.getenv("CV_LOCAL_DEMO_SESSIONS", "0") == "1"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def session_expiry(remember: bool = False) -> datetime:
    if remember and LOCAL_DEMO_SESSIONS:
        return utcnow() + timedelta(days=30)
    return utcnow() + timedelta(hours=SESSION_HOURS)


def create_token(user: User, session: AuthSession) -> str:
    return jwt.encode(
        {"sub": user.id, "sid": session.id, "exp": session.expires_at},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


@dataclass
class AuthContext:
    user: User
    session: AuthSession


def current_auth(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> AuthContext:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["sub"]
        session_id = payload["sid"]
    except (jwt.PyJWTError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    session = db.get(AuthSession, session_id)
    if not session or session.user_id != user_id or session.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Session is no longer active")
    expires_at = session.expires_at.replace(tzinfo=timezone.utc) if session.expires_at.tzinfo is None else session.expires_at
    if expires_at <= utcnow():
        raise HTTPException(status_code=401, detail="Session has expired")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
    if getattr(user, "status", "active") != "active":
        raise HTTPException(status_code=403, detail="Account is not active. Contact an administrator.")
    return AuthContext(user=user, session=session)


def current_user(auth: AuthContext = Depends(current_auth)) -> User:
    return auth.user
