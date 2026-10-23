from io import BytesIO
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from app.main import app
from app.migrations import upgrade_local_schema
from test_rbac_system import make_user


def test_case_configuration_and_clinical_opt_in():
    with TestClient(app) as client:
        _, owner = make_user("configuration-owner@example.org", "researcher")
        _, outsider = make_user("configuration-other@example.org", "researcher")
        payload = {"case_code": "HEPATIC-PREP", "modality": "CT", "anatomy": "hepatic",
                   "intended_task": "volume_preparation", "source_dataset": "MSD Task08", "source_reference": "public-case-001"}
        created = client.post("/api/cases", headers=owner, json=payload)
        assert created.status_code == 201, created.text
        case = created.json()
        assert case["source_dataset"] == "MSD Task08"
        assert case["intended_task"] == "volume_preparation"
        assert case["clinical_metadata_enabled"] is False
        assert case["inference_compatible"] is False
        assert client.get(f"/api/cases/{case['id']}", headers=outsider).status_code == 404
        for invalid in [{**payload, "case_code": "BAD-TASK", "intended_task": "artery_segmentation"},
                        {**payload, "case_code": "BAD-XCA", "modality": "XCA"}]:
            assert client.post("/api/cases", headers=owner, json=invalid).status_code == 422
        assert client.post("/api/cases", headers=owner,
                           json={"case_code": "UNAPPROVED-NOTES", "clinical_notes": "Deidentified research notes"}).status_code == 422
        assert client.patch(f"/api/cases/{case['id']}", headers=owner,
                            json={"medical_history": ["diabetes"]}).status_code == 422
        enabled = client.patch(f"/api/cases/{case['id']}", headers=owner,
                               json={"clinical_metadata_enabled": True, "medical_history": ["diabetes"]})
        assert enabled.status_code == 200, enabled.text
        disabled = client.patch(f"/api/cases/{case['id']}", headers=owner, json={"clinical_metadata_enabled": False})
        assert disabled.json()["medical_history"] == ["diabetes"]  # never erase historical metadata on toggle
        assert client.patch(f"/api/cases/{case['id']}", headers=owner, json={"clinical_metadata_enabled": None}).status_code == 422


def test_configuration_frozen_after_upload_and_legacy_cta_default():
    with TestClient(app) as client:
        _, owner = make_user("configuration-freeze@example.org", "researcher")
        legacy = client.post("/api/cases", headers=owner, json={"case_code": "LEGACY-CTA", "modality": "CTA"})
        assert legacy.status_code == 201
        assert legacy.json()["intended_task"] == "volume_preparation"
        case = client.post("/api/cases", headers=owner, json={"case_code": "FIXED-INPUT"}).json()
        source = BytesIO(); Image.new("L", (64, 64), 100).save(source, format="PNG")
        uploaded = client.post(f"/api/cases/{case['id']}/images", headers=owner,
                               files={"file": ("source.png", source.getvalue(), "image/png")})
        assert uploaded.status_code == 201
        assert client.patch(f"/api/cases/{case['id']}", headers=owner, json={"modality": "CTA"}).status_code == 409
        assert client.patch(f"/api/cases/{case['id']}", headers=owner,
                            json={"intended_task": "artery_segmentation"}).status_code == 409
        assert client.patch(f"/api/cases/{case['id']}", headers=owner,
                            json={"source_dataset": "ARCADE recorded source"}).status_code == 200


def test_additive_local_schema_upgrade_is_repeatable(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as db:
        db.execute(text("CREATE TABLE cases (id VARCHAR(36) PRIMARY KEY, status VARCHAR(32), modality VARCHAR(32))"))
        db.execute(text("CREATE TABLE images (id VARCHAR(36), case_id VARCHAR(36))"))
        db.execute(text("CREATE TABLE users (id VARCHAR(36))"))
        db.execute(text("INSERT INTO cases (id, status, modality) VALUES ('preserved', 'created', 'XCA'), ('volume', 'created', 'CTA')"))
    upgrade_local_schema(engine); upgrade_local_schema(engine)
    with engine.connect() as db:
        rows = db.execute(text("SELECT id, intended_task, source_dataset, clinical_metadata_enabled FROM cases ORDER BY id")).all()
        assert [tuple(row) for row in rows] == [("preserved", "artery_and_stenosis", None, 0), ("volume", "volume_preparation", None, 0)]
    engine.dispose()
