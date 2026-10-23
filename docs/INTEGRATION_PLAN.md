# Incremental integration plan

Prepared after source/model audit, before this phase's implementation. Preserve the application, baseline weights, original metrics and branch `lingareddy-dhanush`. Never publish main, secrets, datasets or checkpoints. Training remains separate; no retraining is necessary for these integration changes.

| Phase | Existing evidence | Work and acceptance gate |
|---|---|---|
| 1–2: audit/registry | Existing two-model release and 12-task research catalog | Four audit documents created first; retain explicit modality/task/metric scopes and blockers |
| 3: jobs | Secure uploads and authorization already exist; synchronous inference only | Add persistent inference job record, single-worker bounded dispatch, idempotency, status/error routes and restart interruption handling; no silent duplicate inference; tests for authorization/failure/repeated requests |
| 4–6: masks/geometry/candidates | Preserved adapters, geometry, overlays and history exist | Keep tensors/thresholds unchanged; persist private discrete masks and raw float scores, candidate coordinates/source mapping, stage QC; verify checkpoint load and synthetic pipeline/history/authorization |
| 7: severity | No validated reference-segment protocol | Safe `insufficient_evidence` interface only; no fabricated narrowing/category. Enabling estimates requires a permitted labelled measurement cohort, validated reference selection and frozen rules |
| 8: result/explanation | Existing measurement sidecar and validation snapshots | Versioned validated structured document, deterministic source-linked sections; original numbers authoritative; tests for missing/failed/skipped fields and historic immutability |
| 9: UI/reports | Existing role workspaces, overlays, revisions/export | Connect job polling and saved explanation/candidate panels; display true states and limitations, reuse existing report permissions and snapshots |
| 10–11: verification/deployment | Prior build and real-model tests pass; two policy failures pre-exist | Run relevant tests/build/full regression; record exact outcomes, restart local app, document single-worker deployment/artifact transfer. Other laptop/manual clinical-image review remain separate acceptance steps |

## Explicit unresolved dependencies

- 3D inference: separate anatomy-specific approved adapters, exact native resampling/inverse geometry, full expected-case acceptance and resource/deployment validation are missing. Keep volume preparation usable; do not load CT weights in XCA.
- Severity/patient confidence: no validated diameter-reference standard or independent permitted patient cohort; raw scores cannot become diagnostic confidence.
- ML training UI: compute/approval/external execution service is not connected. Do not build a fake training button or copy queues into the app.
- Baseline permission-policy tests disagree with existing defaults. Report them without silently broadening or weakening access.
- Secure DICOM intake beyond basic checks requires organization-specific de-identification and burned-in identifier review; other-laptop performance/install remains unverified.
- GitHub write access was denied for both CLI and connected integration. Preserve reviewable local commits; do not bypass restrictions or push main.

## Manual acceptance checklist

Use a permitted de-identified coronary XCA frame or clearly marked synthetic fixture. Login as a case-authorized researcher; upload/confirm metadata; start one job and refresh; inspect actual overlays, candidate coordinates and unit labels; confirm saved evidence/explanation agrees with source fields; rerun with a new key and compare immutable history; verify another user cannot retrieve job or artifacts; exercise corrupt/oversize/wrong-route uploads and missing model; confirm severity is unavailable; review/export a report with the appropriate role; install the pinned archive on the target laptop and repeat. Do not treat synthetic inference as clinical validation.
