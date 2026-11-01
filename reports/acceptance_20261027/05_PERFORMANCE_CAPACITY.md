# Phase 5 — Performance benchmark and capacity plan

Machine evidence: `readiness_benchmark.json`. Command:
`backend/.venv/bin/python scripts/benchmark_readiness.py --pid 88158 --out reports/acceptance_20261027/readiness_benchmark.json`

Read-only local liveness endpoint; 20 requests per concurrency level, 60 total.
All returned HTTP 200. This very short warm-process run is not sustained capacity.

| Concurrent clients | p50 ms | p95 ms | max ms |
| ---: | ---: | ---: | ---: |
| 1 | 0.634 | 0.873 | 9.107 |
| 4 | 1.662 | 2.011 | 2.219 |
| 8 | 2.523 | 3.537 | 4.114 |

API process sampled RSS: 35,168 KiB before, 44,624 KiB after; CPU sample 0.2% at
both points. Samples are not peak memory/utilization. No GPU measurement, model
forward pass, uploaded-storage growth, cold start, 3D inference latency or
long-duration failure rate was measured. HTTP microbenchmark throughput must not
be advertised as inference jobs per second.

Reliability fixtures check queue idempotency, revoked/changed input/model jobs,
failed processing, worker interruption and explicitly requested new runs without
fake completed artifacts. Operational readiness returns failure when dependencies
are unavailable. These are software tests, not live process fault injection.

Capacity plan pending target hardware: retain one API worker/one inference worker
with the current in-process queue; measure 2D/3D workloads separately on target
CPU/GPU, including warm/cold p50/p95, peak RSS/VRAM, queue wait, timeout/recovery,
artifact bytes/job and storage retention. Size storage from measured bytes/job ×
jobs/day × retention days plus backup overhead; no fabricated values supplied.
Before scaling to multiple API workers, use a durable externally coordinated
queue and test duplicate prevention, cancellation/recovery and multi-worker safety.
