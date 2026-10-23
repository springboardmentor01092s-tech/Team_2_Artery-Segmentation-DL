"""Share existing de-identified demo cases with the seeded local demo team.

Run from backend with CV_LOCAL_DEMO_SHARING=1 in the local .env. Existing grants
are kept; the script can be rerun safely.
"""

from sqlalchemy import select

from app.database import SessionLocal
from app.main import share_case_with_demo_team
from app.models import AuditEvent, Case, User


def main() -> None:
    cases_checked = 0
    grants_created = 0
    with SessionLocal() as db:
        for case in db.scalars(select(Case)).all():
            owner = db.get(User, case.owner_id)
            if owner is None:
                continue
            cases_checked += 1
            count = share_case_with_demo_team(case, owner, db)
            if count:
                db.add(AuditEvent(user_id=owner.id, action="demo_case_shared", case_id=case.id))
                grants_created += count
        db.commit()
    print(f"Checked {cases_checked} cases; created {grants_created} demo access grants")


if __name__ == "__main__":
    main()
