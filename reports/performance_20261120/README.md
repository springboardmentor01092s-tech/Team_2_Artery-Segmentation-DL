# Performance measurements: 20 November 2026

Target: merged CoroVision build on `http://127.0.0.1:8000` (Docker, one worker, CPU only, macOS host).
Client: Chrome on the same machine, authenticated administrator session, read-only requests.
Each endpoint was called 25 times after 3 warm-up calls, with `cache: no-store`.

## API response time

| Endpoint | Median | p95 | Failures |
|---|---:|---:|---:|
| `/api/health` | 2.5 ms | 4.7 ms | 0/25 |
| `/api/health/ready` | 2.1 ms | 3.6 ms | 0/25 |
| `/api/auth/me` | 2.5 ms | 3.5 ms | 0/25 |
| `/api/cases` | 2.8 ms | 3.9 ms | 0/25 |
| `/api/dashboard/analytics` | 3.2 ms | 3.7 ms | 0/25 |
| `/api/notifications` | 2.9 ms | 4.0 ms | 0/25 |
| `/api/admin/users` | 4.2 ms | 6.3 ms | 0/25 |
| `/api/admin/audit` | 5.6 ms | 7.1 ms | 0/25 |
| `/api/analysis/status` | 3.6 ms | 4.4 ms | 0/25 |

The administrator account has no case assignments, so `/api/cases` and the dashboard aggregate an empty case list for this account.

## Concurrent users (dashboard analytics endpoint)

| Simultaneous requests | Total time | Succeeded |
|---:|---:|---:|
| 1 | 3 ms | 1/1 |
| 8 | 18 ms | 8/8 |
| 16 | 26 ms | 16/16 |
| 32 | 52 ms | 32/32 |

## Dashboard loading time

Full application page in Chrome: DOMContentLoaded 95 ms, load event 103 ms.

## Image processing, model inference and report generation

These times come from audit-log timestamps of real runs on this installation (one-second resolution):

| Operation | Measured time | Runs |
|---|---:|---:|
| 2D analysis job, request to completion (preprocessing, artery segmentation, stenosis detection, explanations, measurements) | median 18.4 s (8.9–18.4 s) | 2 |
| Upload to analyzed image | 18.4 s | 1 |
| 3D CTA inference, queued to completion (512 × 512 × 321 volume) | 19.9 s | 1 |
| Research report generation after analysis | ≈ 0.1 s | 3 |
| First model-status check after restart (loads checkpoints) | 444 ms max | – |

## GPU utilization

Not applicable on this installation. The Docker build runs inference on CPU and no GPU is attached. GPU utilization must be measured on a GPU host if one is used for deployment.

## Limitations

- Single-machine loopback measurements; network latency of a hosted deployment is not included.
- Analysis times have few samples and one-second timestamp resolution. Inference runs on one worker, so additional jobs queue rather than run in parallel.
