"""One-time local bootstrap: ADMIN_EMAIL=... ADMIN_PASSWORD=... python create_admin.py"""
import os

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import User
from app.security import hash_password

email = os.getenv("ADMIN_EMAIL", "").strip().lower()
password = os.getenv("ADMIN_PASSWORD", "")
if not email or len(password) < 12:
    raise SystemExit("Set ADMIN_EMAIL and ADMIN_PASSWORD (at least 12 characters)")

Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    if db.scalar(select(User).where(User.email == email)):
        raise SystemExit("An account with that email already exists")
    db.add(User(email=email, password_hash=hash_password(password), role="admin"))
    db.commit()
print("Administrator account created")
