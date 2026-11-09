# Milestone closeout evidence · 9 November 2026

## Milestone 2 · Saved width profiles

Chrome opened the exact DCA1 case, image and run in the local application. The browser showed four ordered source-pixel profiles containing 687 samples. After a refresh, the graph points and downloaded JSON were identical. The downloaded object matched the persisted analysis API record. The [browser receipt](WIDTH_PROFILE_BROWSER.json) binds the case, image, run and download SHA-256.

This closes width-profile persistence and export for this run. Independent anatomy and calibrated diameter validation remain open.

## Milestone 4 · Local recovery drill and regression

The first offline snapshot attempt stopped on browser-profile symlinks, as intended by the backup script. For the scoped retry, the app was stopped after checking for pending jobs, the demo browser-profile directory was excluded, and the remaining storage was staged separately. The backup and restore utilities verified 164 SQLite and storage files. The main server resumed on port 8000.

The restored copy booted separately on port 8001 with its inference worker disabled. Absolute image and overlay paths were rebased only in the restored database. The exact DCA1 width-profile browser check produced the same receipt as the main app, and the restored CTA run exported a PDF. SQLite quick check passed. The isolated server was stopped. Private recovery data remains in a temporary directory outside the repository. [Recovery receipt](RECOVERY_DRILL.json)

- Backend from `backend/`: `.venv/bin/python -m pytest -q` returned 231 passes and 5 skipped real-artifact opt-ins. The suite covers authorization, case and run binding, reports, notifications, 3D access and operational contracts.
- Frontend from `frontend/`: `node --test tests/*.test.mjs` returned 20 passes.
- The main server's `/api/health/ready` returned ready with database and inference availability. No new inference ran during this drill.

Target container startup, inference capacity and deployment still require the target environment and a container runtime. This drill validates scoped local recovery.

## Research gates still open

- **Dataset and exposure**. Exact publisher identity, annotation alignment, patient grouping and checkpoint exposure are required for independent evaluation. Saved development comparisons remain valid within their recorded scopes.
- **Localization, measurements and severity**. Expert lesion and vessel references, segment-matched calibration and severity grades remain necessary. The browser and recovery checks establish software behavior.
- **Explainability**. The saved One Touch forward-only occlusion source review records a prepared diagnostic with no integrated provider binding and no attribution maps. Current Kaggle quota, shared ledger and execution lock could not be verified in this session. No diagnostic was dispatched. Complete the runner binding and resource checks before evaluating attribution faithfulness.
- **Detector improvement**. The retained detector remains the accepted research baseline after the rejected refinements. No new candidate was evaluated here.
