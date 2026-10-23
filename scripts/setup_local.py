"""Prepare a private local runtime. Use Python 3.11, 3.12 or 3.13."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]


def runtime_python() -> Path:
    return ROOT / "backend" / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-ai", action="store_true", help="Also install optional PyTorch inference dependencies (large download)")
    parser.add_argument("--demo", action="store_true", help="Create local demo accounts; credentials stay in ignored local storage")
    parser.add_argument("--model-archive", type=Path, help="Install the separately transferred, hash-pinned two-mask model archive (requires --with-ai)")
    args = parser.parse_args()
    if args.model_archive:
        if not args.with_ai:
            parser.error("--model-archive requires --with-ai")
        args.model_archive = args.model_archive.resolve()
        if not args.model_archive.is_file():
            parser.error("Model archive does not exist; transfer it separately before setup")
    if not (3, 11) <= sys.version_info[:2] <= (3, 13):
        raise SystemExit("Use Python 3.11–3.13 for this dependency set (for example python3.13 or py -3.12).")
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    node = shutil.which("node")
    if not npm or not node:
        raise SystemExit("Install Node.js 20+ with npm, then run setup again.")
    major = int(subprocess.check_output([node, "--version"], text=True).strip().lstrip("v").split(".")[0])
    if major < 20:
        raise SystemExit("Node.js 20 or newer is required.")
    python = runtime_python()
    if not python.is_file():
        venv.EnvBuilder(with_pip=True).create(ROOT / "backend" / ".venv")
    subprocess.run([str(python), "-m", "pip", "install", "-r", str(ROOT / "backend" / ("requirements-ai.txt" if args.with_ai else "requirements.txt"))], check=True)
    if args.model_archive:
        subprocess.run([str(python), str(ROOT / "scripts/install_trained_release.py"), "--install", str(args.model_archive)], cwd=ROOT, check=True)
    env_file = ROOT / "backend" / ".env"
    if not env_file.exists():
        # Exclusive creation avoids replacing a user's secrets on a repeated setup.
        with env_file.open("x", encoding="utf-8") as handle:
            handle.write("JWT_SECRET=" + secrets.token_urlsafe(48) + "\nFRONTEND_ORIGIN=http://127.0.0.1:5173\nOAUTH_REDIRECT_BASE=http://127.0.0.1:5173\nCV_LOCAL_DEMO_SESSIONS=0\nCV_LOCAL_DEMO_SHARING=0\n")
        if os.name != "nt":
            env_file.chmod(0o600)
    else:
        print("Keeping existing backend/.env unchanged.")
    for folder in ("uploads", "preprocessed", "analysis"):
        (ROOT / "storage" / folder).mkdir(parents=True, exist_ok=True)
    subprocess.run([npm, "ci"], cwd=ROOT / "frontend", check=True)
    subprocess.run([npm, "run", "build"], cwd=ROOT / "frontend", check=True)
    if args.demo:
        subprocess.run([str(python), "seed_demo_accounts.py"], cwd=ROOT / "backend", check=True)
        print("Demo credentials: backend/demo-credentials.json (private; never commit).")
    if not shutil.which("pdftoppm"):
        print("Optional PDF conversion unavailable: install Poppler to enable scanned PDF uploads.")
    print("Setup complete. Run: python scripts/run_local.py")
    print("Model weights are supplied separately; use --with-ai --model-archive to install the pinned release. Training is not started by setup.")


if __name__ == "__main__":
    main()
