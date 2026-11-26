"""Performance tests: response times. Limits are generous so they pass on a normal laptop CPU."""
import time
from concurrent.futures import ThreadPoolExecutor

import pytest


def _timed(fn):
    start = time.perf_counter()
    result = fn()
    return result, time.perf_counter() - start


def test_login_is_fast_enough(client, users):
    r, t = _timed(
        lambda: client.post(
            "/auth/login", data={"username": users["clinician"]["email"], "password": "Test-pass-123"}
        )
    )
    assert r.status_code == 200
    assert t < 2.0, f"login took {t:.2f}s"


def test_me_endpoint_is_fast(client, users):
    client.get("/auth/me", headers=users["clinician"]["headers"])  # warm up
    r, t = _timed(lambda: client.get("/auth/me", headers=users["clinician"]["headers"]))
    assert r.status_code == 200
    assert t < 0.5, f"/auth/me took {t:.2f}s"


def test_listing_many_cases_is_fast(client, users, make_case):
    for i in range(25):
        make_case(users["clinician"]["headers"], f"perf-{i}")
    r, t = _timed(lambda: client.get("/cases", headers=users["clinician"]["headers"]))
    assert r.status_code == 200
    assert len(r.json()) >= 25
    assert t < 1.0, f"listing cases took {t:.2f}s"


def test_average_response_time_over_20_requests(client, users):
    start = time.perf_counter()
    for _ in range(20):
        assert client.get("/cases", headers=users["clinician"]["headers"]).status_code == 200
    average = (time.perf_counter() - start) / 20
    assert average < 0.3, f"average {average:.3f}s per request"


def test_ten_parallel_users(client, users):
    headers = users["clinician"]["headers"]

    def call(_):
        return client.get("/cases", headers=headers).status_code

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=10) as pool:
        codes = list(pool.map(call, range(30)))
    total = time.perf_counter() - start
    assert all(c == 200 for c in codes), codes
    assert total < 15.0, f"30 requests from 10 threads took {total:.2f}s"


# ------------------------------------------------------------------ heavy operations (use the real models)
@pytest.mark.slow
def test_preprocessing_time(client, e2e_case):
    r, t = _timed(lambda: client.post(f"/cases/{e2e_case['id']}/preprocess", headers=e2e_case["headers"]))
    assert r.status_code == 200
    assert t < 15.0, f"preprocessing took {t:.2f}s"


@pytest.mark.slow
def test_stenosis_pipeline_time(client, e2e_case):
    r, t = _timed(
        lambda: client.post(f"/cases/{e2e_case['id']}/stenosis-pipeline", headers=e2e_case["headers"])
    )
    assert r.status_code == 200
    assert t < 120.0, f"pipeline took {t:.2f}s"
    print(f"\nstenosis pipeline: {t:.1f}s")


@pytest.mark.slow
@pytest.mark.parametrize("fmt,limit", [("json", 5.0), ("csv", 5.0), ("pdf", 20.0)])
def test_report_generation_time(client, e2e_case, fmt, limit):
    r, t = _timed(
        lambda: client.get(
            f"/cases/{e2e_case['id']}/report", params={"format": fmt}, headers=e2e_case["headers"]
        )
    )
    assert r.status_code == 200
    assert t < limit, f"{fmt} report took {t:.2f}s"
    print(f"\n{fmt} report: {t:.2f}s")