from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Notification
from test_rbac_system import make_user


def test_owned_bulk_read_delete_restore_and_atomic_scope():
    with TestClient(app) as client:
        user, headers = make_user("notification-owner@test.org", "viewer")
        other, other_headers = make_user("notification-other@test.org", "viewer")
        with SessionLocal() as db:
            rows = [Notification(user_id=user["id"], message=f"Notice {i}", kind="analysis_ready") for i in range(2)]
            foreign = Notification(user_id=other["id"], message="Private", kind="analysis_ready")
            db.add_all([*rows, foreign]); db.commit()
            ids = [row.id for row in rows]; foreign_id = foreign.id
        url = "/api/notifications/bulk"
        assert client.post(url, headers=headers, json={"ids":[*ids, foreign_id],"action":"delete"}).status_code == 404
        assert len(client.get("/api/notifications", headers=headers).json()) == 2
        assert client.post(url, headers=headers, json={"ids":ids,"action":"read"}).status_code == 200
        assert all(row["read_at"] for row in client.get("/api/notifications",headers=headers).json())
        assert client.post(url, headers=headers, json={"ids":ids,"action":"delete"}).status_code == 200
        assert client.get("/api/notifications",headers=headers).json() == []
        assert len(client.get("/api/notifications?deleted=true",headers=headers).json()) == 2
        assert client.get("/api/notifications?deleted=true",headers=other_headers).json() == []
        assert client.post(url, headers=headers, json={"ids":ids,"action":"delete"}).status_code == 200
        assert client.post(url, headers=headers, json={"ids":ids,"action":"restore"}).status_code == 200
        assert len(client.get("/api/notifications",headers=headers).json()) == 2
        assert client.get("/api/notifications?deleted=true",headers=headers).json() == []
        with SessionLocal() as db:
            assert all(db.get(Notification, value) is not None for value in ids)
        assert client.post(url,headers=headers,json={"ids":[],"action":"delete"}).status_code == 422
        assert client.post(url,json={"ids":ids,"action":"read"}).status_code == 401
