# Research progress dashboard

Added 26 October 2026 under Model Evaluation → Research progress.

## Verified implementation

- Authenticated, read-only evidence endpoint and fixed-allowlist downloads.
- Administrator, researcher and ML engineer access; other roles denied.
- Saved comparison, activity journal, dataset readiness and checkpoint provenance.
- Optional 15-second refresh, suspended while the browser document is hidden.
- Prepared work, rejected experiments and measured improvements are distinct.
- Missing files render unavailable, not zero-valued performance or completed work.

## Verification results

- Backend dashboard tests: 5 passed, covering authorization, missing/corrupt evidence, path isolation, invalid activity and rejected regression.
- Existing frontend tests: 14 passed.
- TypeScript and production Vite build passed; existing large-bundle warning remains.
- Browser verified as an authenticated researcher: original ARCADE baseline/candidate metrics, zero measured improvements, two quarantined checkpoints and evidence-linked activity visible.

## Limitations

No live Kaggle job connector is installed. Refresh reads saved files; it does not start jobs or prove active computation. Activity is explicitly recorded using `scripts/record_research_progress.py` and requires an existing allowlisted evidence file. Future experiments must save evidence and record their result to appear here. Framework checks and downloaded artifacts are not model accuracy improvements. No training, weight changes, activation, deployment or Git push was performed for this dashboard.

The 40 framework checks displayed in the dashboard come from the separate framework verification report, not the five dashboard backend tests. Historical results are development-validation evidence, not clinical validation.

## Live local-worker extension — 26 October

The dashboard now reads real local process heartbeats and completed-sample counts.
A running label requires both a heartbeat no older than 45 seconds and a live PID;
missing/dead/stale workers are explicitly unconfirmed. Terminal completion, failure
and rejection events are recorded automatically with per-job result downloads.
Only the local monitored worker is connected; Kaggle live telemetry remains absent.

The 30-minute continuation was reactivated through the app's existing automation.
It does not authorize retraining, paid resources, overlapping trials or automatic
activation. The first actual monitored job checked 1200 ARCADE stenosis exported
annotation/mask pairs, found zero rasterization mismatches and preserved all labels.
That is a completed prerequisite audit, not a measured accuracy improvement.
