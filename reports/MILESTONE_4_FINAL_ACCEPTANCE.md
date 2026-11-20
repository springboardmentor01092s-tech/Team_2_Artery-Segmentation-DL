# CoroVision AI acceptance closeout · 18 November 2026

Scope follows [the supplied PRD milestones](../docs/reference/CoroVision_AI_Comprehensive_PRD_supplied_2026-10-16.md#22-milestones-and-deliverables). Results below reconcile the existing evidence with the current checkout. IDs are local traceability identifiers.

| Requirement | Milestone | Implementation | Test and actual result | Evidence | Blocker or remaining check | Acceptance |
|---|---|---|---|---|---|---|
| F-01 Data and foundation | 1 | EDA, manifests, architecture, login, authorized case and preprocessing workflows | Local input and role checks passed | [EDA](../docs/DATASET_EDA.md), [architecture](../docs/ARCHITECTURE.md), [browser inputs](INPUT_FORMAT_BROWSER_VERIFICATION.md) | Patient grouping and exposure limits affect independent research | PASS for local foundation |
| F-02 Persistence and recovery | 1 | Local SQLite and fresh PostgreSQL schemas | Local recovery and populated PostgreSQL ORM restore passed | [Recovery and deployment](DEPLOYMENT_READINESS_NOT_DEPLOYED.md) | Legacy PostgreSQL upgrade path is absent. HTTP/report persistence and rollback rehearsal remain open | PARTIAL |
| S-01 Segmentation and visual evidence | 2 | Frozen 2D and 3D segmentation, saved masks and centerlines | Saved 2D and volume workflows passed. Development metrics recorded separately | [Model selection](../docs/MODEL_SELECTION_20261113.md), [browser inputs](INPUT_FORMAT_BROWSER_VERIFICATION.md) | Independent expert masks and native-resolution CTA references | PARTIAL |
| S-02 Vessel measurements | 2 | Source-grid width and diameter with quality gates | Geometry regressions and saved-run abstention verified | [Acceptance matrix](PROJECT_REQUIREMENTS_ACCEPTANCE_MATRIX.md) | Qualified QCA, calibration and independent reference agreement | PARTIAL |
| D-01 Stenosis and severity | 3 | Candidate localization, experimental severity and abstention | Candidate-bound exports preserve eligibility and indeterminate outcomes | [Report evidence](REPORT_DOWNLOAD_CONSISTENCY.md) | Expert localization, MLD/RVD and matched severity grades | PARTIAL |
| D-02 Explainability | 3 | Run-linked activation and candidate Grad-CAM where available | Existing perturbation evidence has mixed results | [Engineering audit](APPLICATION_FINAL_ENGINEERING_AUDIT.md) | Complete insertion and randomization evidence | PARTIAL |
| R-01 Reports and exports | 4 | Immutable 2D snapshots, volume exports and protected downloads | PNG and saved CTA browser exports reconciled. XA DICOM and CTA PDFs passed visual inspection. All-format 2D and 3D API authorization checks passed | [Report evidence](REPORT_DOWNLOAD_CONSISTENCY.md), [ledger](PROJECT_CONTINUATION_LEDGER.md) | Deployed access checks remain open | PASS for tested local scope |
| R-02 Dashboards and roles | 4 | Case, analysis, evaluation, admin and report workspaces | Prior focused dashboard/registry/roles/evaluation/report suite passed 12 tests | [Browser audit](BROWSER_INTERACTION_AUDIT.md), [ledger](PROJECT_CONTINUATION_LEDGER.md) | Exhaustive control, keyboard, responsive and admin browser acceptance remains open | PARTIAL |
| R-03 Model evaluation and selection | 4 | Versioned retained models and development metrics | Prior checkpoint hashes and selection rationale preserved. Kaggle v2 has no usable sweep output | [Registry](../docs/MODEL_REGISTRY.md), [selection](../docs/MODEL_SELECTION_20261113.md), [ledger](PROJECT_CONTINUATION_LEDGER.md) | A completed frozen-checkpoint sweep and documented selection decision | PARTIAL |
| R-04 Tests, latency and monitoring | 4 | Regression, health routes, logging and audit events | Last full regression recorded 330 backend passes, 5 skips and 20 frontend passes. New local liveness check returned 60/60 HTTP 200 | [Ledger](PROJECT_CONTINUATION_LEDGER.md), [operations](../docs/OPERATIONS_AND_READINESS.md) | Dashboard timing, inference and report latency under load, CPU/GPU peaks, worker failure and alert checks | PARTIAL |
| R-05 Containers and deployment readiness | 4 | Dockerfile and Compose configuration | Prior Compose configuration passed. Current Docker daemon probe failed with missing socket | [Deployment readiness](DEPLOYMENT_READINESS_NOT_DEPLOYED.md) | BLOCKED_BY_ENVIRONMENT for image build, scan, restart and persistence tests | BLOCKED |
| R-06 Actual deployment | 4 | Setup and deployment documentation | Target verification has not been performed | [Deployment readiness](DEPLOYMENT_READINESS_NOT_DEPLOYED.md) | Hosting target and explicit deployment authorization | NOT_TESTED |
| R-07 Final handoff | 4 | README, architecture, quickstart, admin/access, API and demo documentation | Existing documentation and demo evidence inventoried | [Handoff](../docs/FINAL_PROTOTYPE_HANDOFF.md), [demo](../docs/LOCAL_DEMO_RUN.md) | Final presentation and full live demonstration acceptance | PARTIAL |

## Local performance check

Run from the checkout with the existing app listening on port 8000:

`python3 scripts/benchmark_readiness.py --out /private/tmp/corovision-m4-closeout-20261118.json`

| Concurrent clients | Requests passed | Median | p95 |
|---|---:|---:|---:|
| 1 | 20/20 | 0.58 ms | 0.91 ms |
| 4 | 20/20 | 1.42 ms | 2.05 ms |
| 8 | 20/20 | 2.25 ms | 2.90 ms |

These measurements cover loopback liveness GETs. Dashboard, inference, report generation, GPU usage and deployment performance still need separate measurement.

## Acceptance decisions

- Milestone 1 **PARTIAL** overall. Local foundation passes, with PostgreSQL upgrade and rollback open.
- Milestones 2 and 3 **PARTIAL**. Development workflows are demonstrated, with independent segmentation, measurement, severity and attribution evidence outstanding.
- Milestone 4 **PARTIAL**. Local reports and focused regression pass. Browser, documentation and operational items remain open as listed above.
- Model evaluation and selection **PARTIAL**. The retained baselines have development evidence. Threshold selection and protected evaluation remain open. No new optimizer run occurred.
- Deployment readiness **BLOCKED** for runtime acceptance. Actual deployment **NOT_TESTED**.
- Independent research validation **BLOCKED** on eligible unseen-patient data and qualified references. Clinical validation **BLOCKED** on scientific evidence and governance.
- Full original project acceptance **PARTIAL**. Current scope remains a research demonstration.
