"""Keep API tests isolated from the development database and uploads."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

_temp = TemporaryDirectory()
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_temp.name) / 'test.db'}"
os.environ["STORAGE_DIR"] = str(Path(_temp.name) / "storage")
os.environ["JWT_SECRET"] = "test-only-secret-value"
os.environ["COROVISION_MODEL_PROVIDER"] = "legacy"  # Unit tests do not consume developer-installed weights.
os.environ["COROVISION_INFERENCE_WORKER"] = "0"  # Queue tests dispatch deterministically unless explicitly enabled.


def authorize_test_researcher(email: str):
    """Explicit elevated fixture for image-workflow tests, not registration policy."""
    from sqlalchemy import select
    from app.database import SessionLocal
    from app.models import User
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None
        user.role = "researcher"
        db.commit()


def pytest_sessionfinish(session, exitstatus):
    # Release pooled SQLite handles before TemporaryDirectory cleanup on Windows.
    from app.database import engine
    engine.dispose()
