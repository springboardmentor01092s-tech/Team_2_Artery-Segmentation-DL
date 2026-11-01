# Connected-drive integration verification — 25 October 2026

## Changes and commands

- Read-only handoff audit: scripts/audit_connected_handoff.py, output
  reports/connected_handoff_audit.json: nine packages, 15 evidence hashes matched,
  all 12 indexed checkpoint files available. Not a full raw-dataset rescan.
- SHA-256 of both drive baseline weights exactly matched both installed files and
  ml/releases/corovision_20261023.json. No duplicate weights copied or overwritten.
- scripts/import_handoff_evaluation.py imported real artery baseline records:
  23 epochs and 200 per-image numeric validation records. Idempotent source/hash
  check; imported status experimental; no approval, artifacts or performance invented.
- preprocessing.py now supports exact PIL.ImageOps.pad/BILINEAR for preserved XCA
  uploads, including correct upscaling, centering, inverse geometry and spacing.
  Existing previews are retained; non-512 legacy previews must be re-uploaded.
  Enhanced/ROI and high-bit-depth-normalized inputs are blocked from preserved
  inference because their contracts are not validated.
- No training configuration, pooling, split membership or baseline weight changed.

## Executed tests

1. Full backend regression suite: **86 passed, 2 opt-in tests skipped**, 55.97 s.
2. Opt-in installed-weight tests plus input-contract parity:
   **12 passed**, 10.95 s. Includes real models through synchronous and queued
   API paths, saved artifacts, access control and exact preprocessing parity.
3. Public ARCADE validation image 1 (source SHA-256
   748a2d4fcd2df8a11e5c1b836abbdf5201d21f75be808e0e71865ef8cda7bf55):
   **1 passed**, 5.76 s, real checkpoints through upload/worker/result/artifacts.
4. Live acceptance run created PUBLIC-ARCADE-CHECK-5ddc8f under the existing
   Clinician demo account. Completed job, verified artery/stenosis masks, raw
   scores and overlay. Receipt: reports/public_image_integration_receipt.json.
5. Browser opened that persisted result: completed status, correct model version,
   actual overlay/candidate, 8,927 artery pixels, 833 stenosis pixels, 797.96 px
   algorithmic centerline length and insufficient-evidence severity. Values are
   research outputs on one development-exposed image, NOT validation performance.
   Screenshot saved as /tmp/corovision-verified-drive-inference.png.

Warnings remain: test fixture JWT key length, Starlette/httpx deprecation and Pillow
mode deprecation. No failed tests in these final executed runs.

## Genuinely integrated stages

| Stage | Current verified state |
| --- | --- |
| Case / upload / persistent worker | Verified with public source image and authorization checks |
| 2D artery checkpoint | Exact installed/drive hash, loader resize parity, real output saved/displayed |
| Vessel geometry | Mask-derived 2D centerline/branches/length/diameter; pixel units without calibration |
| Stenosis checkpoint | Image-based instance masks/candidate bounds and raw scores; no confirmed-disease claim |
| Vessel-conditioned detector | Not integrated; current detector does not consume vessel feature tensors |
| Severity / clinical grade | Blocked: validated local/reference measurement protocol unavailable |
| 3D live inference | Not integrated or approved; volume review/preparation is not model inference |
| Evaluation history | Real artery training/validation records imported; further task reports need independent contract mapping |
| Explanations | Deterministic from persisted structured results; no independent LLM diagnosis |

## Review gate and remaining actions

Review DATASET_COMPATIBILITY_REPORT.md before any training adapter/configuration
change. Licenses, unknown patient mappings and cross-dataset overlap remain blocking
issues for pooling. Checkpoint presence/selected_for_integration is not approval.
Additional 3D models require exact source adapters, native geometry parity,
resource limits, per-task acceptance policies and explicit authorized review.
Remote Kaggle old/new account mapping and live GPU monitoring have not been
verified; no login/password, remote job or retraining was needed for this increment.
