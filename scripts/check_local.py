"""Read-only health check for a running local CoroVision installation."""
import json
import re
from urllib.error import URLError
from urllib.request import urlopen


def main():
    try:
        with urlopen("http://127.0.0.1:8000/api/health", timeout=10) as response:
            health = json.load(response)
        with urlopen("http://127.0.0.1:8000/", timeout=10) as response:
            page = response.read().decode()
        if health.get("status") != "ok" or '<div id="root">' not in page:
            raise SystemExit("Health check failed: API or built frontend is unavailable.")
        assets = set(re.findall(r'(?:src|href)="(/[^\"]+)"', page))
        assets.add("/corovision-heart-mark.png")
        for path in assets:
            with urlopen("http://127.0.0.1:8000" + path, timeout=10) as response:
                if response.status != 200:
                    raise SystemExit(f"Missing frontend asset: {path}")
        print("API: healthy | Frontend: available")
        print("Inference models:", "available" if health.get("models_ready") else "not installed (upload/preprocessing can still be used)")
    except (URLError, ValueError) as error:
        raise SystemExit(f"Start the app with python scripts/run_local.py first. {error}")


if __name__ == "__main__":
    main()
