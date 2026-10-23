"""Exercise setup without downloading dependencies or modifying the real runtime."""
import importlib.util
import os
from pathlib import Path
import sys


def test_setup_preserves_private_configuration_and_skips_training(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[2] / "scripts/setup_local.py"
    spec = importlib.util.spec_from_file_location("portable_setup", source)
    setup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(setup)
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    monkeypatch.setattr(setup.sys, "version_info", (3, 13, 0))
    python = setup.runtime_python()
    python.parent.mkdir(parents=True)
    python.touch()
    monkeypatch.setattr(sys, "argv", [str(source)])
    monkeypatch.setattr(setup.shutil, "which", lambda name: None if name == "pdftoppm" else f"/fake/{name}")
    monkeypatch.setattr(setup.subprocess, "check_output", lambda *args, **kwargs: "v22.0.0")
    commands = []
    monkeypatch.setattr(setup.subprocess, "run", lambda command, **kwargs: commands.append(command))
    setup.main()
    env = tmp_path / "backend/.env"
    original = env.read_bytes()
    assert b"JWT_SECRET=" in original
    assert b"CV_LOCAL_DEMO_SHARING=0" in original
    assert (tmp_path / "storage/uploads").is_dir()
    assert not any("train_" in str(command) or "seed_demo_accounts" in str(command) for command in commands)
    if os.name != "nt":
        assert env.stat().st_mode & 0o077 == 0
    setup.main()
    assert env.read_bytes() == original
