"""Idempotent SQLite upgrades for the local research prototype."""
from sqlalchemy import text


ADDITIONS = {
    'volume_analyses': {'input_kind': "VARCHAR(32) DEFAULT 'unspecified'",'model_key':"VARCHAR(64) DEFAULT 'imagecas'"},
    "clinical_reviews": {"analysis_event_id": "VARCHAR(36)", "image_id": "VARCHAR(36)"},
    "cases": {
        "modalities_json": "TEXT",
        "intended_tasks_json": "TEXT",
        "intended_task": "VARCHAR(40) DEFAULT 'artery_and_stenosis'",
        "source_dataset": "VARCHAR(120)",
        "source_reference": "VARCHAR(200)",
        "clinical_metadata_enabled": "BOOLEAN DEFAULT 0",
        "patient_code": "VARCHAR(40)",
        "age_band": "VARCHAR(20)",
        "gender": "VARCHAR(20)",
        "medical_history": "TEXT",
        "risk_factors": "TEXT",
        "clinical_notes": "TEXT",
        "scan_date": "VARCHAR(10)",
        "workflow_status": "VARCHAR(32) DEFAULT 'draft'",
        "processing_status": "VARCHAR(32) DEFAULT 'not_started'",
        "report_status": "VARCHAR(32) DEFAULT 'draft'",
        "report_version": "INTEGER DEFAULT 0",
        "report_approved_by": "VARCHAR(36)",
        "report_approved_at": "DATETIME",
        "deleted_at": "DATETIME",
    },
    "images": {
        "processed_spacing_mm": "VARCHAR(80)",
        "roi_box": "VARCHAR(80)",
        "frame_index": "INTEGER",
        "page_index": "INTEGER",
        "preprocessing_json": "TEXT",
        "preprocessing_config_json": "TEXT",
        "source_sha256": "VARCHAR(64)",
        "processed_sha256": "VARCHAR(64)",
    },
    "users": {
        "status": "VARCHAR(20) DEFAULT 'active'",
        "can_approve_reports": "BOOLEAN DEFAULT 0",
    },
}


def upgrade_local_schema(engine):
    if engine.dialect.name != "sqlite":
        return
    with engine.begin() as connection:
        for table, columns in ADDITIONS.items():
            existing = {row[1] for row in connection.execute(text(f"PRAGMA table_info({table})"))}
            if not existing:
                continue  # Tables absent in older partial schemas are created by metadata.create_all.
            new_workflow_column = table == "cases" and "workflow_status" not in existing
            new_processing_column = table == "cases" and "processing_status" not in existing
            new_task_column = table == "cases" and "intended_task" not in existing
            for name, type_name in columns.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {type_name}"))
            if new_workflow_column:
                connection.execute(text("""
                    UPDATE cases SET workflow_status = CASE
                      WHEN status LIKE 'reviewed:%' THEN 'reviewed'
                      WHEN status = 'analyzed' THEN 'pending_review'
                      WHEN status = 'uploaded' THEN 'ready_for_analysis'
                      ELSE 'draft' END
                """))
            if new_processing_column:
                connection.execute(text("""
                    UPDATE cases SET processing_status = 'completed'
                    WHERE status IN ('uploaded', 'analyzed') OR status LIKE 'reviewed:%'
                """))
            if new_task_column and "modality" in existing:
                connection.execute(text("UPDATE cases SET intended_task = 'volume_preparation' WHERE modality IN ('CT', 'CTA', 'MRA', 'MRI')"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_images_case_source_sha256 ON images (case_id, source_sha256)"))
