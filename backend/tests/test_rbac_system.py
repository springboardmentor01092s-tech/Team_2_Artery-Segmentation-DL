from fastapi.testclient import TestClient
from app.database import SessionLocal
from app.main import app
from app.models import User, Case, CaseAccess, ClinicalReview
from app.security import hash_password


from sqlalchemy import select

def make_user(email: str, role: str, status: str = "active", password: str = "secure-pass-1234") -> tuple[dict, dict]:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(email=email, password_hash=hash_password(password), role=role, status=status)
            db.add(user)
            db.commit()
            db.refresh(user)
        user_id = user.id
    with TestClient(app) as client:
        token = client.post("/api/auth/login", json={"email": email, "password": password}).json().get("access_token")
        return {"id": user.id, "email": email, "role": role, "status": status}, {"Authorization": f"Bearer {token}"}


def test_5_roles_permission_matrix():
    with TestClient(app) as client:
        admin, admin_hdr = make_user("admin-rbac@test.org", "admin")
        doctor, doc_hdr = make_user("doctor-rbac@test.org", "doctor")
        researcher, res_hdr = make_user("res-rbac@test.org", "researcher")
        technician, tech_hdr = make_user("tech-rbac@test.org", "technician")
        viewer, view_hdr = make_user("viewer-rbac@test.org", "viewer")

        # 1. Admin Management
        assert client.get("/api/admin/users", headers=admin_hdr).status_code == 200
        assert client.get("/api/admin/users", headers=doc_hdr).status_code == 403
        assert client.get("/api/admin/users", headers=res_hdr).status_code == 403
        assert client.get("/api/admin/users", headers=tech_hdr).status_code == 403
        assert client.get("/api/admin/users", headers=view_hdr).status_code == 403

        # 2. Case Creation
        c_doc = client.post("/api/cases", headers=doc_hdr, json={"case_code": "DOC-001"}).json()["id"]
        c_tech = client.post("/api/cases", headers=tech_hdr, json={"case_code": "TECH-001"}).json()["id"]
        c_res = client.post("/api/cases", headers=res_hdr, json={"case_code": "RES-001"}).json()["id"]

        # A clinical role needs explicit review access on another user's case.
        read_share = client.post(
            f"/api/cases/{c_tech}/access", headers=tech_hdr,
            json={"user_email_or_id": doctor["email"], "access_level": "read"},
        )
        assert read_share.status_code == 201
        read_only_case = client.get(f"/api/cases/{c_tech}", headers=doc_hdr)
        assert read_only_case.status_code == 200
        assert read_only_case.json()["permissions"]["can_review"] is False
        assert client.post(
            f"/api/cases/{c_tech}/review", headers=doc_hdr,
            json={"decision": "reviewed"},
        ).status_code == 403
        review_share = client.post(
            f"/api/cases/{c_tech}/access", headers=tech_hdr,
            json={"user_email_or_id": doctor["email"], "access_level": "review"},
        )
        assert review_share.status_code == 201
        assert client.get(f"/api/cases/{c_tech}", headers=doc_hdr).json()["permissions"]["can_review"] is True
        
        # Viewer cannot create cases
        v_create = client.post("/api/cases", headers=view_hdr, json={"case_code": "VIEW-001"})
        assert v_create.status_code == 403

        # 3. Clinical Review & Decision (Doctor only)
        review_doc = client.post(
            f"/api/cases/{c_doc}/review",
            headers=doc_hdr,
            json={"decision": "approved", "stenosis_severity": "mild", "notes": "No significant luminal reduction."},
        )
        assert review_doc.status_code == 201
        assert review_doc.json()["status"] == "reviewed:approved"
        assert len(review_doc.json()["reviews"]) == 1

        # Non-doctors cannot record clinical review
        assert client.post(
            f"/api/cases/{c_tech}/review",
            headers=tech_hdr,
            json={"decision": "approved"},
        ).status_code == 403
        assert client.post(
            f"/api/cases/{c_res}/review",
            headers=res_hdr,
            json={"decision": "approved"},
        ).status_code == 403
        assert client.post(
            f"/api/cases/{c_doc}/review",
            headers=view_hdr,
            json={"decision": "approved"},
        ).status_code == 403

        # 4. Case Access Sharing
        share_res = client.post(
            f"/api/cases/{c_doc}/access",
            headers=doc_hdr,
            json={"user_email_or_id": viewer["email"], "access_level": "read"},
        )
        assert share_res.status_code == 201

        # Viewer can now view the assigned case
        viewer_case = client.get(f"/api/cases/{c_doc}", headers=view_hdr)
        assert viewer_case.status_code == 200
        assert viewer_case.json()["permissions"]["can_edit"] is False
        assert viewer_case.json()["permissions"]["can_upload"] is False
        assert viewer_case.json()["permissions"]["can_run_analysis"] is False
        assert client.get(f"/api/cases/{c_doc}", headers=doc_hdr).json()["permissions"]["can_assign"] is True

        # 5. Export Case (Admin, Doctor, Researcher only)
        # Administrative privileges alone do not grant medical-data access.
        assert client.get(f"/api/cases/{c_doc}/export", headers=admin_hdr).status_code == 404
        assert client.get(f"/api/cases/{c_doc}", headers=admin_hdr).status_code == 404
        assert client.post(f"/api/cases/{c_doc}/access", headers=doc_hdr,
                           json={"user_email_or_id": admin["email"], "access_level": "read"}).status_code == 201
        assert client.get(f"/api/cases/{c_doc}/export", headers=admin_hdr).status_code == 200
        _, approver = make_user("operational-approver@test.org", "admin")
        assert client.post(f"/api/admin/users/{admin['id']}/operational-grant", headers=approver,
                           json={"permission": "analysis:export", "enabled": True,
                                 "reason": "Authorized de-identified case export for audited operational support."}).status_code == 200
        assert client.get(f"/api/cases/{c_doc}/export", headers=admin_hdr).status_code == 200
        assert client.get(f"/api/cases/{c_doc}/export", headers=doc_hdr).status_code == 200
        assert client.get(f"/api/cases/{c_res}/export", headers=res_hdr).status_code == 200
        assert client.get(f"/api/cases/{c_doc}/export", headers=tech_hdr).status_code == 403
        assert client.get(f"/api/cases/{c_doc}/export", headers=view_hdr).status_code == 403


def test_account_suspension_and_status():
    with TestClient(app) as client:
        admin, admin_hdr = make_user("admin-status@test.org", "admin")
        user, user_hdr = make_user("target-user@test.org", "researcher")

        # Active user can get profile
        assert client.get("/api/auth/me", headers=user_hdr).status_code == 200

        # Admin suspends user
        resp = client.post(f"/api/admin/users/{user['id']}/status", headers=admin_hdr, json={"status": "suspended"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "suspended"

        # User's active session is revoked (returns 401)
        assert client.get("/api/auth/me", headers=user_hdr).status_code in (401, 403)

        # New login is blocked with 403
        login_resp = client.post("/api/auth/login", json={"email": user["email"], "password": "secure-pass-1234"})
        assert login_resp.status_code == 403

        # Admin reactivates user
        reactivate = client.post(f"/api/admin/users/{user['id']}/status", headers=admin_hdr, json={"status": "active"})
        assert reactivate.status_code == 200
        assert reactivate.json()["status"] == "active"

        # Login works again
        new_token = client.post("/api/auth/login", json={"email": user["email"], "password": "secure-pass-1234"}).json()["access_token"]
        assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {new_token}"}).status_code == 200


def test_local_demo_team_sees_shared_case_updates(monkeypatch):
    monkeypatch.setenv("CV_LOCAL_DEMO_SHARING", "1")
    with TestClient(app) as client:
        _, clinical_hdr = make_user("radiologist.demo@example.com", "clinician")
        _, doctor_hdr = make_user("doctor.demo@example.com", "doctor")
        _, research_hdr = make_user("researcher.demo@example.com", "researcher")
        _, technician_hdr = make_user("technician.demo@example.com", "technician")
        _, viewer_hdr = make_user("viewer.demo@example.com", "viewer")
        _, ml_hdr = make_user("mlengineer.demo@example.com", "ml_engineer")
        _, outsider_hdr = make_user("unassigned-viewer@example.com", "viewer")

        created = client.post("/api/cases", headers=clinical_hdr, json={"case_code": "SHARED-DEMO-001"})
        assert created.status_code == 201
        case_id = created.json()["id"]
        doctor_case = client.get(f"/api/cases/{case_id}", headers=doctor_hdr)
        assert doctor_case.status_code == 200
        assert doctor_case.json()["permissions"]["can_edit"] is True
        assert doctor_case.json()["permissions"]["can_review"] is True
        assert client.get(f"/api/cases/{case_id}", headers=technician_hdr).json()["permissions"]["can_upload"] is True
        assert client.get(f"/api/cases/{case_id}", headers=viewer_hdr).json()["permissions"]["can_edit"] is False
        assert client.get(f"/api/cases/{case_id}", headers=outsider_hdr).status_code == 404
        assert client.get("/api/cases", headers=ml_hdr).status_code == 403

        changed = client.patch(f"/api/cases/{case_id}", headers=doctor_hdr, json={"gender": "unknown"})
        assert changed.status_code == 200
        reviewed = client.post(f"/api/cases/{case_id}/review", headers=doctor_hdr,
                               json={"decision": "reviewed", "notes": "Reviewed shared demo study"})
        assert reviewed.status_code == 201
        updated_review = client.post(f"/api/cases/{case_id}/review", headers=doctor_hdr,
                                     json={"decision": "needs_followup", "notes": "Updated shared demo review"})
        assert updated_review.status_code == 201
        for headers in (clinical_hdr, research_hdr, technician_hdr, viewer_hdr):
            case = client.get(f"/api/cases/{case_id}", headers=headers).json()
            assert case["gender"] == "unknown"
            assert case["latest_review"]["notes"] == "Updated shared demo review"
            assert case["status"] == "reviewed:needs_followup"
