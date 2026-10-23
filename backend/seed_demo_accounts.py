"""Create missing local demo accounts with generated passwords.

Run from the backend directory: python3 seed_demo_accounts.py
Existing accounts and passwords are preserved. The generated credential file is
Git-ignored. POSIX uses owner-only permissions; Windows inherits the backend
directory's filesystem access controls.
"""

import json
import os
import secrets
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select

load_dotenv(Path(__file__).resolve().parent / ".env", override=False)

from app.database import Base, SessionLocal, engine
from app.models import AuditEvent, User, UserIdentity, UserProfile
from app.security import hash_password


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "demo-credentials.json"
ACCOUNTS = (
    ("Radiologist / Clinician", "clinician", "radiologist_demo", "radiologist.demo@example.com", "Demo Radiologist"),
    ("Doctor / Clinical Reviewer", "doctor", "doctor_demo", "doctor.demo@example.com", "Demo Doctor"),
    ("Medical Researcher", "researcher", "researcher_demo", "researcher.demo@example.com", "Demo Researcher"),
    ("Data Scientist / ML Engineer", "ml_engineer", "mlengineer_demo", "mlengineer.demo@example.com", "Demo ML Engineer"),
    ("Technician / Data Operator", "technician", "technician_demo", "technician.demo@example.com", "Demo Technician"),
    ("Viewer / Student", "viewer", "viewer_demo", "viewer.demo@example.com", "Demo Viewer"),
    ("Administrator", "admin", "admin_demo", "admin.demo@example.com", "Demo Administrator"),
)


def main() -> None:
    existing = json.loads(OUTPUT.read_text()) if OUTPUT.exists() else {"site": "http://127.0.0.1:5173/", "accounts": []}
    accounts = list(existing.get("accounts", []))
    saved_emails = {item["email"] for item in accounts}
    Base.metadata.create_all(bind=engine)
    created = 0
    with SessionLocal() as db:
        for label, role, username, email, display_name in ACCOUNTS:
            if email in saved_emails:
                if not db.scalar(select(User).where(User.email == email)):
                    raise SystemExit(f"Saved account {email} is missing from the database; no accounts created")
                continue
            if db.scalar(select(User).where(User.email == email)):
                raise SystemExit(f"Demo account {email} exists without saved credentials; refusing to reset its password")
            if db.scalar(select(UserIdentity).where(UserIdentity.username == username)):
                raise SystemExit(f"Demo username {username} already exists; no accounts created")
            password = secrets.token_urlsafe(18)
            user = User(email=email, password_hash=hash_password(password), role=role)
            db.add(user)
            db.flush()
            db.add(UserProfile(user_id=user.id, display_name=display_name))
            db.add(UserIdentity(user_id=user.id, username=username))
            db.add(AuditEvent(user_id=user.id, action="demo_account_created"))
            accounts.append({"role": label, "backend_role": role, "username": username,
                             "email": email, "password": password})
            created += 1

        if not created:
            print(f"All {len(accounts)} local demo accounts already exist")
            return
        fd, temporary = tempfile.mkstemp(prefix=".demo-credentials.", dir=HERE)
        try:
            if hasattr(os, "fchmod"):
                os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w") as output:
                json.dump({"site": existing.get("site", "http://127.0.0.1:5173/"), "accounts": accounts}, output, indent=2)
                output.write("\n")
            db.commit()
            os.replace(temporary, OUTPUT)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    print(f"Created {created} local demo accounts; {len(accounts)} total; credentials saved to {OUTPUT}")


if __name__ == "__main__":
    main()
