# Model Evaluation Dashboard — audit and incremental implementation

Audit date: 2026-10-24. Implementation checkout: dedicated application repository
(`.git-publish`); branch `lingareddy-dhanush`. No training or promotion is authorized.

## Phase 1 — repository findings

- Frontend: React 19, TypeScript, Vite; App.tsx uses role-scoped SidebarView navigation,
  not a URL router. PrismUI Card/Button and existing theme CSS are used.
  ModelWorkspace.tsx and ModelAnalytics.tsx already display recorded release metrics,
  task disclosures, comparison reports, coverage charts and readiness snapshots.
- Backend: FastAPI; SQLAlchemy with SQLite default and environment-selected database.
  models.py stores users, sessions, grants, cases, images, analysis jobs/runs/events,
  reviews and audit events. AnalysisRun/AnalysisEvent are case inference records,
  NOT training/evaluation runs and must not be counted as such.
- Auth: current_user/require_roles enforce server-side role gates. Existing model
  status/registry access: administrator, researcher, ML engineer. Case artifact routes
  separately check case authorization; ML access is not patient-case access.
- Existing APIs: GET /api/analysis/status, GET /api/analysis/models,
  POST /api/analysis/models/activate (admin only). Preserved-release mode blocks
  legacy activation. Activation is not evidence of a documented approval decision.
- Persisted release: ml/releases/corovision_20261023.json contains two hash-pinned
  checkpoints, architecture, input size, thresholds, validation image counts,
  Dice and IoU. resnet34_unet is binary artery; maskrcnn_resnet50_fpn is stenosis.
  Their tasks and metric aggregation differ; they are not comparable architectures.
- ml/releases/research_evidence_20261023.json records 12 task narratives, shared
  cohort limitations, two prepared-grid calibration studies and training-workspace
  report references. Those referenced files are not necessarily in this checkout.
  Never turn missing references into clickable local-file URLs.
- Optional legacy reports are loaded from models/segmentation and
  models/arcade_instances by analysis_status. Missing files currently yield empty
  reports. No epoch-level history, reference/prediction evaluation samples or
  patient-independent split audit was found in the application release.
- Inference checkpoints live under ignored models/trained_release and are verified
  by trained_release.py; CPU inference is serialized. Storage and database paths
  are environment configured. Private case probability/mask artifacts are served
  by authenticated existing routes. No evaluation ground truth is implied.
- Training notebooks/runners were intentionally removed from this application-only
  branch. Training remains external and paused; no training URL was supplied.
- Existing tests include model registry/RBAC, trained-release integrity, inference
  pipeline and case artifact access. No durable experiment or approval schema exists.

## Architecture and data contracts

Add a read-only evaluation catalog adapter over the pinned release manifest.
Keep original files untouched. Catalog entries are imported report records, not
newly executed evaluations. Null means not recorded, never zero.

EvaluationRun: stable record ID, model metadata, task, dataset, split,
sample counts and units, protocol, metric definitions/aggregation, checkpoint hash,
source reference, timestamp nullable, approval status nullable, runtime nullable.
EpochMetric, SampleEvaluation, PredictionArtifact, ErrorAnalysis and ModelApproval
remain explicitly unavailable until a validated importer and durable storage exist.
Do not infer these from prose, file timestamps, current inference or active status.

API: GET /api/evaluation/runs and /api/evaluation/runs/{id}, gated to existing
model-manager roles. JSON export uses this same authenticated catalog data.
No arbitrary server path or artifact URL is accepted. No case data is included.

## Phases and acceptance gates

1. Audit/plan: this file; completed.
2. Typed catalog: real release records, definitions, nulls, RBAC and detail endpoint.
3. Explorer: summary cards, search, task/architecture filtering, stable sorting,
   pagination, selected record details and JSON report download.
4. Training/comparison: keep existing report charts; compatibility requires exact
   task, dataset version, split and protocol. Missing protocol blocks direct ranking.
   Epoch curves require imported epoch records, not interpolation.
5. Dataset analysis: show separate evidence/support strings, shared-cohort caveats;
   split counts, leakage, annotation audits require actual dataset manifests.
6. Prediction/error review: reuse authorized viewer only for case inference;
   evaluation review needs sample-level reference/prediction bindings, coordinate
   frames and matching rules. No fake overlay or 3D evaluation viewer.
7. Approval/history: needs persistent candidate state, predeclared criteria,
   authorized reviewer decisions, audit transactions and server-side promotion gate.
   Do not expose a cosmetic approve button or label active models approved.
8. Exports/accessibility: catalog JSON export, semantic controls/tables, responsive
   panels, existing theme; detailed evidence stays collapsible.
9. Verification: automated catalog mapping, nulls, report preservation, unknown IDs,
   authorized roles, denied roles and frontend build; browser interaction checks.

## Remaining blockers

Provide versioned epoch histories, comparable candidate reports with evaluation
protocols, dataset/split manifests, de-identified evaluation artifacts and per-sample
metrics. Supply approved research acceptance criteria and reviewer authority policy.
Provide training environment URL/agent separately. Raw training reference paths
are provenance, not proof that artifacts are available to this app.

This increment does not claim full completion of phases 4–7 or live monitoring.

## Increment verification and phase report

- Phase 1 completed: repository audit and this plan.
- Phase 2 completed for the pinned release: evaluation_catalog.py plus authenticated
  list/detail routes in main.py; typed evaluationData.ts. No new runs executed.
- Phase 3 completed for imported release records: EvaluationExplorer.tsx provides
  counts, search, filters, sorting, pagination, multi-selection and report details.
- Phase 4 partial: existing comparison charts preserved; new comparison guard rejects
  distinct tasks and missing dataset/protocol versions. Epoch logs remain unavailable.
- Phases 5–7 partial: dedicated sections explain exact missing inputs. No dataset audit,
  prediction evaluator or approval workflow is claimed. Existing records are preserved.
- Phase 8 partial: filtered JSON export implemented; browser download verified with
  one artery record and exact manifest Dice. Responsive width checked at 1654px:
  document width 1639px, no horizontal page overflow. Mobile/dark QA not yet executed.
- Phase 9 executed: 4 backend tests passed across test_evaluation_catalog.py and
  test_dashboard_model_registry.py; 3 frontend data tests passed; production build
  passed. Browser verified filter, report details, comparison rejection and export.
- Non-failing warnings: existing test JWT fixture key length, Starlette/httpx deprecation;
  Vite reports a large bundle. No failures in executed tests.
- Backend restarted to load new read-only endpoints. No training, activation, database
  migration, checkpoint overwrite, Git commit or push was performed.

Changed sources: backend/app/evaluation_catalog.py, backend/app/main.py,
backend/tests/test_evaluation_catalog.py, frontend/src/evaluationData.ts,
frontend/src/EvaluationExplorer.tsx, frontend/src/ModelWorkspace.tsx,
frontend/src/model-workspace.css and frontend/tests/evaluation-data.test.mjs.

## Remaining-phase implementation — subsequent increment

The earlier partial-phase notes above describe the first increment only. The
following infrastructure now exists; actual external experiment contents are
still required and have not been fabricated.

| Phase | Implemented workflow | Verification / remaining input |
| --- | --- | --- |
| 1 | Repository audit and scope boundaries | Existing manifest/registry paths inspected |
| 2 | Strict, typed immutable experiment import and persisted SQL tables | Finite metrics, schema, artifacts and role checks tested |
| 3 | Imported experiment overview, report selector, search and pinned-report pagination | Real pinned records retained; imported experiment list currently empty |
| 4 | Epoch traces, exact values, best/stop markers, loss-gap plot, compatible candidate deltas and ratio bars | Requires externally recorded epoch/experiment data |
| 5 | Dataset counts, annotation/class distributions, exclusions, prevalence and split/audit provenance | Displays imported audits; does not invent a patient-leakage audit |
| 6 | Authenticated 2D PNG and bounded 3D NPY slice layers, zoom/scroll-pan, opacity, failure navigation, sample errors and distributions | Backend image/slice/mismatched-reference tests; real review artifacts not imported |
| 7 | Immutable predeclared policies, importer submission, independent admin gates, persisted sample reviews and append-only decisions | Threshold, role, self-review and status-transition tests passed |
| 8 | JSON report/schema downloads, accessible labelled controls, collapsible pinned details and existing theme styles | No raw image bytes in ordinary JSON export |
| 9 | Full backend regression suite and frontend tests/build | 81 passed, 1 opt-in model test skipped; 9 frontend tests passed |

New implementation: backend/app/evaluation_workspace.py, persisted entities in
backend/app/models.py, frontend/src/ExperimentLab.tsx and corresponding CSS,
backend/tests/test_evaluation_workspace.py. main.py includes the protected router.
ML navigation now names Model Evaluation; Deployment Candidates opens the new lab.

Read docs/EVALUATION_IMPORT_AND_REVIEW.md for the external-laptop import contract.
No training runner, dataset, real experiment, candidate approval, model activation
or checkpoint overwrite was created by this implementation. New SQL tables were
created through the existing idempotent startup after a SQLite backup.

Important limitations: live training/GPU telemetry still needs an external agent
and destination; no training URL was supplied. Imported metrics are provenance-
labelled reports, not independently recomputed scientific evaluations. Large
native-volume review beyond the bounded NPY contract needs an object-storage/
streaming adapter. Full clinical or institution-isolated production certification
is not implied. Missing real logs/labels cannot be completed through UI code.
