"""Launch the built application and API together on localhost; no training."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    python = ROOT / "backend" / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file() or not (ROOT / "frontend/dist/index.html").is_file() or not (ROOT / "backend/.env").is_file():
        raise SystemExit("Run python scripts/setup_local.py first.")
    if not 1 <= args.port <= 65535:
        raise SystemExit("Port must be between 1 and 65535.")
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", args.port)) == 0:
            raise SystemExit(f"Port {args.port} is in use. Stop the other server or use --port.")
    # Serving the built frontend from FastAPI avoids two-server configuration.
    # api.ts uses a separate API port only for the Vite development server.
    if args.port != 8000:
        raise SystemExit("The built application currently expects port 8000; use the default port.")
    print(f"Application: http://127.0.0.1:{args.port}", flush=True)
    print(f"API docs: http://127.0.0.1:{args.port}/docs", flush=True)
    command = [str(python), "-m", "uvicorn", "app.main:app", "--app-dir", str(ROOT / "backend"), "--host", "127.0.0.1", "--port", str(args.port)]
    process = subprocess.Popen(command, cwd=ROOT)
    try:
        raise SystemExit(process.wait())
    except KeyboardInterrupt:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == "__main__":
    main()
