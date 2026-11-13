# Fresh application and model-evaluation audit — 13 November 2026

This audit verifies current software execution and evidence display. It does not convert development metrics into independent or clinical validation.

## Fresh commands and results

- Full backend regression: `296 passed, 5 skipped` in 72.18 seconds. Skips are explicit opt-in hardware/checkpoint paths, not silent failures.
- Focused installed-checkpoint, notifications, registry, reports, security and container-contract suite: `37 passed, 2 skipped` in 23.79 seconds. The two skips are separately exercised by the task-adapter run below.
- All connected task adapters with installed checkpoints: `8 passed` in 26.87 seconds, including original ImageCAS/ImageCAS-X execution without cross-task substitution.
- Frontend TypeScript and Vite production build: passed; 2,406 modules transformed. The existing large-bundle advisory remains.
- Git whitespace validation: passed.

## Live application evidence

- 2D run `6f7660c2-651a-45ff-8604-c81de77b6e4f` displays original/processed images, artery mask, overlay, centerline, boundary, probability maps, four width profiles and three run-bound candidates.
- 3D run `d0fbbf42-e090-4fb5-a586-65eaab605321` completed in 7.89 seconds for a 512 × 512 × 321 volume and displays orthogonal overlays, a 360-degree viewer and JSON/CSV/PDF research exports.
- 3D vessel graph, stenosis, diameter and severity remain explicitly unavailable/not assessable rather than receiving substituted 2D outputs.

## Corrected stale test

The installed-release smoke test expected the historical 12-task registry. The current registry contains 14 records: ten connected hash-verified inference routes, two excluded hepatic tasks and two intentionally unconnected ensemble proposals. The assertion now verifies the exact `14 total / 10 connected` contract. No model, checkpoint or patient data changed.

## Software tasks verified

- Binary/instance segmentation execution and saved artifacts.
- Metric/report separation and immutable exports.
- Role-scoped notification provenance and deduplication.
- Hash-pinned model versioning, activation history and rollback controls.
- RBAC, upload-to-saved-output, invalid-input, reporting, real 2D/3D inference and static packaging safeguards.

Independent patient performance, calibrated physical diameter, severity agreement, attribution faithfulness, compatible pooling/ensemble benefit and deployed-container capacity remain open.
