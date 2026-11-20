# Milestone compliance · 20 November 2026

Audit target: local `lingareddy-dhanush` (`f2ea58743af251706bc4d509e140321cf024bb18` plus local changes). Local remote-tracking refs show `origin/main` contains only LICENSE and `origin/review` is a distinct revision. These refs were not refreshed. The supplied local PRD §5 is Global Application Shell and Navigation; the attachment uses a different numbering scheme. Coverage below follows the requested subject areas. Percent complete is **not assessable** for each milestone because the full requirement denominator and live proof were not reconciled. It is not a test pass percentage.

| Requirement group | Status | Evidence | Gap / fix |
|---|---|---|---|
| M1 objectives, workflow, architecture, wireframes, EDA | Partial | Local PRD §§3, 5, 22 and DCA1 attribution file | Reconcile original design and EDA artifacts to the specification |
| M1 auth, RBAC, profile, sessions and audit | Partial | Auth modules and current isolated regression suite | Full role/operation and browser matrix |
| M1 case history, metadata, upload and preprocessing | Partial | `backend/app/main.py` upload handler, `test_direct_dicom_intake.py` | Verify history comparison, reject-upload behavior and all format variants |
| M2 baseline, advanced and trained models | Partial | `backend/app/trained_release.py`, `test_trained_release.py`, Docker checkpoint hash evidence | Reconcile each named architecture and comparable selection result |
| M2 masks, postprocessing, centerline, branches and diameter | Partial | 2D Docker saved artifacts, `test_saved_measurement.py`, geometry tests | Independent native-grid mask and physical-reference agreement |
| M2 multi-model comparison and scores | Partial | ModelWorkspace and ExperimentLab | Independently recompute scores and reconcile pooled versus per-image aggregation |
| M3 stenosis extraction, localization and dashboard | Partial | Preserved stenosis checkpoint and public Docker zero-candidate run | Positive-candidate browser acceptance |
| M3 percentage narrowing, categories and calibration | Partial | Saved measurement, protocol authorization and stenosis measurement tests | Expert same-frame reference agreement; current no-detection remains ungraded |
| M3 Grad-CAM, feature activation, attention and comparison | Partial | Frozen foreground target test and saved Docker feature activation | Grad-CAM++ and attention-gate coverage not established; faithfulness remains open |
| M4 dashboard, reports, exports and comparison | Partial | Reporting tests and prior authenticated Docker CTA downloads | Exact version reconciliation, 2D and browser retest |
| M4 performance, operations, Docker and deployment | Partial | Fresh local standard profile ready, 338 backend tests | Load, recovery, release security and hosted gates remain |
| M4 hosted cloud | Missing in audited setup | Local-only Compose | Select and authorize target |
| Alerts, model management and advanced techniques | Partial | Audit/notifications and model workspace present | Severity alert levels, promotion/rollback and technique-by-technique audit not verified |
| Training and evaluation module | Partial | ExperimentLab imports results; seven `research_training/` entries tracked in current checkout and origin/review | Reconcile branch publishing policy with tracked runners; no training executed |
| Stack | Partial | Default Compose uses SQLite; React/FastAPI and Docker directly inspected | PostgreSQL production topology and each optional tooling substitution need separate verification |
| Section 9 metrics | Partial | Saved metrics and runtime evidence exist | Individual segmentation/detection/severity/system metrics and independent recomputation not tested in this pass |
