"""Bounded local liveness performance and passive header checks."""
from concurrent.futures import ThreadPoolExecutor
import json
import time
from urllib.error import HTTPError
from urllib.request import urlopen

BASE = "http://127.0.0.1:18087"


def fetch(path):
    started = time.perf_counter()
    try:
        response = urlopen(BASE + path, timeout=5)
    except HTTPError as error:
        response = error
    with response:
        response.read()
        return response.status, dict(response.headers.items()), (time.perf_counter() - started) * 1000


status, headers, _ = fetch("/api/health/live")
headers = {key.lower(): value for key, value in headers.items()}
assert status == 200
for key, value in {
    "cache-control": "no-store",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
}.items():
    assert headers.get(key) == value, key
for route in ("/api/auth/me", "/api/cases", "/api/admin/users"):
    assert fetch(route)[0] in {401, 403}, route

rows = []
for workers in (1, 4, 8):
    with ThreadPoolExecutor(max_workers=workers) as pool:
        batch = list(pool.map(fetch, ["/api/health/live"] * 20))
    assert all(status == 200 for status, _, _ in batch)
    times = sorted(elapsed for _, _, elapsed in batch)
    rows.append({"clients": workers, "requests": len(times), "p95_ms": round(times[18], 3)})
print(json.dumps({"passive_headers": "PASS", "anonymous_route_denial": "PASS", "liveness_batches": rows}, indent=2))
