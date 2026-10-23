"""Identity aliases, one-time codes, and confidential OAuth web flows."""

import hashlib
import hmac
import os
import re
import secrets
import smtplib
from datetime import timedelta, timezone
from email.message import EmailMessage
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import AuditEvent, AuthSession, OAuthIntent, OAuthTicket, OneTimeCode, SocialAccount, User, UserIdentity, UserProfile, now
from .security import SECRET_KEY, create_token, current_user, hash_password, session_expiry, verify_password

router = APIRouter(prefix="/api/auth")
USERNAME = re.compile(r"^[a-z][a-z0-9_.-]{2,39}$")
GENERIC_RESET = "If that verified contact belongs to an account, a code has been sent."
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:5173").rstrip("/")
OAUTH_REDIRECT_BASE = os.getenv("OAUTH_REDIRECT_BASE", FRONTEND_ORIGIN).rstrip("/")


def normalized_username(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    value = value.strip().lower()
    if not USERNAME.fullmatch(value):
        raise HTTPException(422, "Username must start with a letter and contain 3–40 letters, numbers, dots, underscores, or hyphens")
    return value


def resolve_user(identifier: str, db: Session) -> User | None:
    identifier = identifier.strip().lower()
    if "@" in identifier:
        return db.scalar(select(User).where(User.email == identifier))
    identity = db.scalar(select(UserIdentity).where(UserIdentity.username == identifier))
    return db.get(User, identity.user_id) if identity else None


class IdentifiersIn(BaseModel):
    username: str | None = None
    current_password: str


@router.patch("/identifiers")
def update_identifiers(data: IdentifiersIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(403, "Current password is incorrect")
    username = normalized_username(data.username)
    if username and db.scalar(select(UserIdentity).where(UserIdentity.username == username, UserIdentity.user_id != user.id)):
        raise HTTPException(409, "Username already in use")
    identity = db.get(UserIdentity, user.id)
    if not identity:
        identity = UserIdentity(user_id=user.id)
        db.add(identity)
    identity.username = username
    db.add(AuditEvent(user_id=user.id, action="identifiers_updated"))
    db.commit()
    return {"username": identity.username}


def identity_out(user: User, db: Session) -> dict:
    item = db.get(UserIdentity, user.id)
    return {"username": item.username if item else None}


def email_ready() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM"))


@router.get("/capabilities")
def capabilities():
    return {"google": provider_ready("google"), "institutional_sso": False,
            "email_reset": email_ready()}


def send_code(destination: str, code: str, purpose: str):
    if not email_ready():
        raise HTTPException(503, "Email delivery is not configured")
    message = EmailMessage()
    message["From"] = os.environ["SMTP_FROM"]
    message["To"] = destination
    message["Subject"] = f"CoroVision AI {purpose} code"
    message.set_content(f"Your CoroVision AI {purpose} code is {code}. It expires in 10 minutes. If you did not request this, ignore this message.")
    host, port = os.environ["SMTP_HOST"], int(os.getenv("SMTP_PORT", "587"))
    try:
        if port == 465:
            connection = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            connection = smtplib.SMTP(host, port, timeout=10)
            connection.starttls()
        with connection:
            if os.getenv("SMTP_USERNAME"):
                connection.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
            connection.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise HTTPException(503, "Email delivery failed; try again later") from exc


def code_digest(user_id: str, purpose: str, code: str) -> str:
    return hmac.new(SECRET_KEY.encode(), f"{user_id}:{purpose}:{code}".encode(), hashlib.sha256).hexdigest()


def issue_code(db: Session, user: User, purpose: str, destination: str):
    recent = db.scalars(select(OneTimeCode).where(
        OneTimeCode.user_id == user.id, OneTimeCode.purpose == purpose,
        OneTimeCode.created_at > now() - timedelta(hours=1),
    ).order_by(OneTimeCode.created_at.desc())).all()
    if recent and (recent[0].created_at.replace(tzinfo=timezone.utc) if recent[0].created_at.tzinfo is None else recent[0].created_at) > now() - timedelta(seconds=60):
        raise HTTPException(429, "Please wait before requesting another code")
    if len(recent) >= 5:
        raise HTTPException(429, "Too many code requests; try again later")
    code = f"{secrets.randbelow(1000000):06d}"
    send_code(destination, code, purpose.replace("_", " "))
    challenge = OneTimeCode(user_id=user.id, purpose=purpose, destination=destination,
                            digest=code_digest(user.id, purpose, code), expires_at=now() + timedelta(minutes=10))
    db.add(challenge)
    db.add(AuditEvent(user_id=user.id, action=f"{purpose}_requested"))
    db.commit()


def consume_code(db: Session, user: User, purpose: str, code: str) -> OneTimeCode:
    challenge = db.scalar(select(OneTimeCode).where(
        OneTimeCode.user_id == user.id, OneTimeCode.purpose == purpose,
        OneTimeCode.consumed_at.is_(None),
    ).order_by(OneTimeCode.created_at.desc()))
    if not challenge:
        raise HTTPException(400, "Invalid or expired code")
    expires = challenge.expires_at.replace(tzinfo=timezone.utc) if challenge.expires_at.tzinfo is None else challenge.expires_at
    if expires <= now() or challenge.attempts >= 5:
        raise HTTPException(400, "Invalid or expired code")
    challenge.attempts += 1
    if not hmac.compare_digest(challenge.digest, code_digest(user.id, purpose, code)):
        db.commit()
        raise HTTPException(400, "Invalid or expired code")
    challenge.consumed_at = now()
    return challenge


class ResetRequestIn(BaseModel):
    contact: EmailStr


class ResetConfirmIn(BaseModel):
    contact: EmailStr
    code: str = Field(pattern=r"^\d{6}$")
    new_password: str = Field(min_length=12, max_length=128)


@router.post("/password-reset/request")
def request_password_reset(data: ResetRequestIn, db: Session = Depends(get_db)):
    contact = data.contact.strip().lower()
    if not email_ready():
        raise HTTPException(503, "Email delivery is not configured")
    user = db.scalar(select(User).where(User.email == contact))
    if user:
        try:
            issue_code(db, user, "password_reset", contact)
        except HTTPException as exc:
            if exc.status_code != 429:
                raise
    return {"detail": GENERIC_RESET}


@router.post("/password-reset/confirm")
def confirm_password_reset(data: ResetConfirmIn, db: Session = Depends(get_db)):
    contact = data.contact.strip().lower()
    user = db.scalar(select(User).where(User.email == contact))
    if not user:
        raise HTTPException(400, "Invalid or expired code")
    challenge = consume_code(db, user, "password_reset", data.code)
    if challenge.destination != contact:
        raise HTTPException(400, "Invalid or expired code")
    user.password_hash = hash_password(data.new_password)
    for session in db.scalars(select(AuthSession).where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))):
        session.revoked_at = now()
    db.add(AuditEvent(user_id=user.id, action="password_reset"))
    db.commit()
    return {"detail": "Password reset. Sign in with your new password."}


PROVIDERS = {
    "google": ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"),
}


def provider_ready(provider: str) -> bool:
    return provider in PROVIDERS and all(os.getenv(key) for key in PROVIDERS[provider])


def callback_url(provider: str) -> str:
    return f"{OAUTH_REDIRECT_BASE}/api/auth/oauth/{provider}/callback"


def authorization_url(provider: str, state: str) -> str:
    if not provider_ready(provider):
        raise HTTPException(503, f"{provider.title()} sign-in is not configured")
    client_id = os.environ[PROVIDERS[provider][0]]
    params = {"client_id": client_id, "redirect_uri": callback_url(provider), "state": state, "response_type": "code"}
    if provider == "google":
        params.update({"scope": "openid email profile", "prompt": "select_account"})
        base = "https://accounts.google.com/o/oauth2/v2/auth"
    return f"{base}?{urlencode(params)}"


def create_oauth_intent(db: Session, provider: str, user_id: str | None = None) -> str:
    state = secrets.token_urlsafe(32)
    db.add(OAuthIntent(id=hashlib.sha256(state.encode()).hexdigest(), provider=provider,
                       user_id=user_id, expires_at=now() + timedelta(minutes=10)))
    db.commit()
    return state


def set_state_cookie(response: Response, request: Request, provider: str, state: str):
    response.set_cookie("cv_oauth_state", f"{provider}:{state}", max_age=600, httponly=True,
                        secure=request.url.scheme == "https", samesite="lax", path="/api/auth/oauth")
    response.headers["Cache-Control"] = "no-store"


@router.get("/oauth/{provider}/start")
def oauth_start(provider: str, request: Request, db: Session = Depends(get_db)):
    if not provider_ready(provider):
        raise HTTPException(503, f"{provider.title()} sign-in is not configured")
    state = create_oauth_intent(db, provider)
    response = RedirectResponse(authorization_url(provider, state), status_code=302)
    set_state_cookie(response, request, provider, state)
    return response


@router.post("/oauth/{provider}/link/start")
def oauth_link_start(provider: str, request: Request, response: Response,
                     user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not provider_ready(provider):
        raise HTTPException(503, f"{provider.title()} sign-in is not configured")
    state = create_oauth_intent(db, provider, user.id)
    set_state_cookie(response, request, provider, state)
    return {"authorization_url": authorization_url(provider, state)}


@router.get("/social-accounts")
def social_accounts(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return {"providers": [item.provider for item in db.scalars(select(SocialAccount).where(SocialAccount.user_id == user.id))]}


def provider_identity(provider: str, code: str) -> tuple[str, str, str]:
    if provider not in PROVIDERS:
        raise HTTPException(400, "Unsupported sign-in provider")
    client_id = os.environ[PROVIDERS[provider][0]]
    client_secret = os.environ[PROVIDERS[provider][1]]
    payload = {"client_id": client_id, "client_secret": client_secret, "code": code,
               "redirect_uri": callback_url(provider)}
    try:
        with httpx.Client(timeout=10) as client:
            if provider == "google":
                result = client.post("https://oauth2.googleapis.com/token", data={**payload, "grant_type": "authorization_code"})
                result.raise_for_status()
                token = result.json()["access_token"]
                profile = client.get("https://openidconnect.googleapis.com/v1/userinfo", headers={"Authorization": f"Bearer {token}"})
                profile.raise_for_status()
                data = profile.json()
                if data.get("email_verified") is not True:
                    raise ValueError("Unverified Google email")
                return str(data["sub"]), str(data["email"]).lower(), str(data.get("name", ""))[:100]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(400, "Social sign-in failed or verified email unavailable") from exc


@router.get("/oauth/{provider}/callback")
def oauth_callback(provider: str, request: Request, code: str | None = None, state: str | None = None,
                   db: Session = Depends(get_db)):
    cookie = request.cookies.get("cv_oauth_state", "")
    if not provider_ready(provider) or not code or not state or not hmac.compare_digest(cookie, f"{provider}:{state}"):
        raise HTTPException(400, "Invalid OAuth callback")
    intent = db.get(OAuthIntent, hashlib.sha256(state.encode()).hexdigest())
    if not intent or intent.provider != provider or intent.consumed_at is not None:
        raise HTTPException(400, "Invalid OAuth callback")
    intent_expiry = intent.expires_at.replace(tzinfo=timezone.utc) if intent.expires_at.tzinfo is None else intent.expires_at
    if intent_expiry <= now():
        raise HTTPException(400, "Invalid OAuth callback")
    intent.consumed_at = now()
    subject, email, name = provider_identity(provider, code)
    account = db.scalar(select(SocialAccount).where(SocialAccount.provider == provider, SocialAccount.subject == subject))
    if intent.user_id:
        if account and account.user_id != intent.user_id:
            raise HTTPException(409, "This social account is already linked to another user")
        user = db.get(User, intent.user_id)
        if not user:
            raise HTTPException(400, "Account unavailable")
        if not account:
            db.add(SocialAccount(user_id=user.id, provider=provider, subject=subject))
            db.add(AuditEvent(user_id=user.id, action=f"{provider}_linked"))
        db.commit()
        response = RedirectResponse(f"{FRONTEND_ORIGIN}/?oauth_linked={provider}", status_code=302)
        response.delete_cookie("cv_oauth_state", path="/api/auth/oauth")
        response.headers["Cache-Control"] = "no-store"
        return response
    if account:
        user = db.get(User, account.user_id)
    else:
        if db.scalar(select(User).where(User.email == email)):
            response = RedirectResponse(f"{FRONTEND_ORIGIN}/?auth_error=existing_account", status_code=302)
            response.delete_cookie("cv_oauth_state", path="/api/auth/oauth")
            return response
        user = User(email=email, password_hash=hash_password(secrets.token_urlsafe(48)), role="viewer")
        db.add(user)
        db.flush()
        db.add(UserProfile(user_id=user.id, display_name=name))
        db.add(SocialAccount(user_id=user.id, provider=provider, subject=subject))
        db.add(AuditEvent(user_id=user.id, action=f"{provider}_registered"))
    if not user:
        raise HTTPException(400, "Social account is unavailable")
    ticket = secrets.token_urlsafe(32)
    db.add(OAuthTicket(id=hashlib.sha256(ticket.encode()).hexdigest(), user_id=user.id,
                       expires_at=now() + timedelta(minutes=2)))
    db.add(AuditEvent(user_id=user.id, action=f"{provider}_login"))
    db.commit()
    response = RedirectResponse(f"{FRONTEND_ORIGIN}/?auth_ticket={ticket}", status_code=302)
    response.delete_cookie("cv_oauth_state", path="/api/auth/oauth")
    response.headers["Cache-Control"] = "no-store"
    return response


class TicketIn(BaseModel):
    ticket: str


@router.post("/oauth/exchange")
def exchange_oauth_ticket(data: TicketIn, db: Session = Depends(get_db)):
    ticket = db.get(OAuthTicket, hashlib.sha256(data.ticket.encode()).hexdigest())
    if not ticket or ticket.consumed_at is not None:
        raise HTTPException(400, "Invalid or expired sign-in ticket")
    expires = ticket.expires_at.replace(tzinfo=timezone.utc) if ticket.expires_at.tzinfo is None else ticket.expires_at
    if expires <= now():
        raise HTTPException(400, "Invalid or expired sign-in ticket")
    user = db.get(User, ticket.user_id)
    if not user:
        raise HTTPException(400, "Account unavailable")
    ticket.consumed_at = now()
    session = AuthSession(user_id=user.id, expires_at=session_expiry(remember=True))
    db.add(session)
    db.commit()
    return {"access_token": create_token(user, session), "token_type": "bearer", "expires_at": session.expires_at}
