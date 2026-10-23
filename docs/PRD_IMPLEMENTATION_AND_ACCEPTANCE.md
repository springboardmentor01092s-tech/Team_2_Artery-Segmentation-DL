# PRD implementation plan and acceptance checklist

16 October 2026. The original reconciliation below is a target plan. A subsequent
[foundation increment](PRD_APPLICATION_CHANGES_2026-10-16.md) implements case
task/source/anatomy configuration, default-disabled clinical context and sectioned
case navigation with tests. The remaining target checklist is not globally passed.

## Repository audit

| Area | Existing evidence | Remaining work |
|---|---|---|
| Auth and RBAC | main.py, auth_ext.py, action_policy.py; isolated auth/role tests | Security hardening, real institution provider, explicit refresh design if needed |
| Role workspaces | RoleWorkspace.tsx, ViewerWorkspace.tsx, App.tsx | Genuine module routes rather than capability cards pointing to shared tools |
| Cases | CaseIn/CasePatch, cases/case_access, CaseWorkflow.tsx | Task/source/subject schema, broad anatomy, complete filters/pagination and default-disabled sensitive demo fields |
| Upload and preparation | preprocessing.py, volume engine, protected source/preview, standard-preset tests | General asset typing/quarantine, persistent volumes, atomic duplicate safeguards |
| Analysis | Synchronous analyze endpoint and saved analysis/events | Persistent jobs, restricted worker, attempts, restart recovery and truthful status |
| Compare and review | Comparison API, overlays, clinical_reviews/report_revisions | Complete side-by-side compatible comparison, version-linked research review decisions/assignment queue |
| Datasets and EDA | Audit scripts, reports and manifests | Database registry, structured findings, scoped API and EDA UI |
| Models | Registry read and admin research activation | Immutable registration/submission/scoped approval workflow |
| Reports | Case export and revision decisions | Complete generated PDF pipeline, preview, failure/retry lifecycle |
| Operations | Health/audit/notifications | Real queue health, storage/retention/backups and restricted service identity |

The previous 29-test preprocessing/workflow run and frontend build are historical
evidence, not fresh verification of these new target requirements. No checklist
below is marked passed solely because an endpoint or a navigation label exists.

## Requirement conflicts resolved

1. Later four professional roles extend the earlier three-role illustration.
   Keep existing viewer/technician and doctor/clinician aliases. Do not bulk-change
   roles or introduce a privileged reviewer through public registration.
2. Keep least-privilege admin operational grants and case assignments even where
   the illustrative matrix says admins can create cases.
3. Do not replace React/FastAPI/SQLAlchemy or current `/api` contracts. Suggested
   endpoints are proposals; preserve working callers.
4. Quarantine counts and dataset warnings require supporting manifests. The
   pasted claim of 48 AortaSeg pairs is not established by the inspected local
   evidence. Distinguish byte hashes, decoded hashes, image IDs and filenames.
5. Preserve UI decisions: viewer simplicity, bell notifications, Settings themes
   at the bottom. Coloured EDA is compatible with neutral app themes and does not
   recolour medical overlay meanings.
6. The reattached comprehensive PRD is now preserved and mapped in the
   [source reconciliation](PRD_SOURCE_RECONCILIATION_2026-10-16.md). Its dataset
   tables/sample metrics remain reported evidence until manifests/logs verify them.

## File by file incremental plan

### Phase A core contracts and case completion

- `backend/app/models.py` plus a new versioned migrations directory: additive
  source/task/subject/update fields and collision-reviewed unique constraints.
- `backend/app/main.py` and `action_policy.py`: input contracts, compatible case
  routing, subject-field controls and authorized filtering/pagination.
- `frontend/src/App.tsx`, `caseTypes.ts`, `CaseWorkflow.tsx`: corresponding form
  fields, task/source metadata, clear validation and preserved filters.
- `backend/tests/`: tests for all professional roles, viewer/technician regression,
  unauthorized case access, optional/default-disabled clinical fields, refresh,
  collisions and modality/anatomy/task rejection.
- Preserve the working sign-in → case → upload → preview journey before widening
  the interface. Do not migrate real data until isolated migration tests pass.

### Phase B durable assets and inference jobs

- New `backend/app/assets.py`, `jobs.py`, `worker.py` (proposed filenames), ORM
  migrations and schemas: typed assets, validation/quarantine, frozen submission,
  attempts, idempotency, durable result and restart recovery.
- Adapt existing inference into a callable service without changing scientific
  outputs or mixing modalities; maintain the old API during a controlled migration.
- New frontend job views/hooks and task selector: render real persisted status;
  never add fake progress, retry or cancellation buttons.
- Test failure, duplicate/concurrent submission, interrupted workers, revoked
  access and refresh recovery using mocks. Real training remains paused.

### Phase C review comparison and report generation

- Extend result/review/report schemas and add result-version assignment/decision
  services. Preserve current clinical records; no silent enum reinterpretation.
- Extend analysis viewer with independent reference/prediction layers, compatibility
  warnings, side-by-side provenance and actual reference-based metrics.
- Add PDF generation, frozen report snapshot, safe protected download and audited
  export. Failure retains a record; retries retain attempt history.
- Test unauthorized review/sign/export, inaccessible stale links, history after
  refresh, PDF completeness and unavailable metric handling.

### Phase D dataset registry EDA and experiments

- New dataset/manifest/finding/experiment services and migration; import only
  audited local records with source evidence and explicit approval state.
- New frontend registry/EDA pages using real authorized API data and accessible
  charts. Keep descriptive distributions separate from model performance.
- Add leak/quarantine issue workflows and reproducible exports. Re-audit supplied
  numeric findings before presenting them as verified.
- Freeze test manifests, record sampling units/aggregation and test non-comparable
  benchmark rejection. Do not initiate training through registry import.

### Phase E advanced analysis and operations

- Scoped model registration/approval, worker health, safe failure/retry tools,
  approved retention/backups, security/performance testing and supported 3D viewer.
- Severity and calibrated measurements require validated inputs/methods and
  task-specific evaluation before enabling. Blood-flow claims remain excluded.
- Production authentication/storage/observability require deployment-specific
  configuration and review. Do not provision services or spend compute implicitly.
- Preserve source roadmap outcomes for relative weeks 1–8 without claiming dates
  or completed milestones. Include optional container/CI/deployment evidence and
  measured performance targets before deployment acceptance.

## Acceptance checklist and evidence requirements

All items below are target checks, currently unchecked pending a dedicated
acceptance run. Existing tests may support them but do not prove full coverage.

### Access and users

- [ ] Each professional role reaches the correct workspace; viewer and technician
  remain appropriately limited. Evidence: browser role walkthrough and API tests.
- [ ] Unauthorized API requests and stale/revoked sessions are rejected.
- [ ] Unassigned cases, assets, results, reports and notification details remain
  inaccessible, including guessed IDs and direct download routes.
- [ ] Role, grant and administrative changes are audited; no self-elevation.
- [ ] Password hashing, expiry, reset/change and session revocation are tested.

### Cases and intake

- [ ] A permitted user creates a unique stable case and reopens it after refresh.
- [ ] Modality, acquisition date, anatomy, intended task and source are supported
  and validated; unknown metadata is not fabricated.
- [ ] Subject metadata is optional, appropriately restricted and disabled for
  ordinary demo use unless explicitly enabled for a legitimate purpose.
- [ ] Original bytes are preserved; content validation rejects malformed files.
- [ ] Geometry mismatches are detected and quarantined where applicable.
- [ ] Preprocessing settings, outputs, version, checksums and units are retained.

### Analysis and results

- [ ] Only compatible assets/tasks/models are accepted on the server.
- [ ] Persistent queued/running/completed/failed jobs survive refresh and recovery.
- [ ] Idempotency and retry attempts preserve history and avoid duplicate work.
- [ ] Predictions, references and derived inputs are distinguishable.
- [ ] Previous analyses reopen and compatible results compare side by side.
- [ ] Metrics state sample count, unit, split, aggregation, reference and protocol;
  missing references do not generate invented scores.
- [ ] Available probability outputs, threshold/post-processing and original versus
  transformed annotation diagnostics retain correct coordinates and class mapping.
- [ ] Vessel/centerline/branch/tortuosity outputs identify method, units and known
  limitations; unsupported severity/flow/capacity measurements are not presented.

### Reviews and exports

- [ ] Assigned reviewers record explicit result-version decisions and comments.
- [ ] Report approval is separately authorized; admin is not automatic reviewer.
- [ ] PDF reports include provenance, units, limitations and research disclaimer.
- [ ] Downloads and exports enforce access and record an audit event.
- [ ] Historical results, failures and decisions remain available without silent
  overwrites when corrected or retried.

### EDA and reliability

- [ ] EDA charts use actual records, readable colours, axes, units, sample counts,
  legends and explanatory captions.
- [ ] Supported dataset overlap/quarantine findings have evidence and visible
  limitations; unresolved patient independence remains labelled unverified.
- [ ] EDA counts are not represented as model accuracy; test data is not tuned on.
- [ ] Loading/empty/error/permission states, keyboard controls and narrow layouts
  work across the affected role views and saved themes.
- [ ] Relevant isolated backend tests, configured lint/type checks and frontend
  production build pass, with warnings and missing tools recorded honestly.
- [ ] Any in-scope Docker/CI/deployment workflow is reproducible with persistent
  storage, managed secrets and recovery checks; performance targets use profiling.

## This consolidation verification

Reviewed the pasted specification, reattached 25-section comprehensive PRD,
current role-policy docs, ORM/auth/case schemas, route declarations, inference
execution and existing frontend workspace mappings.
Checked that this documentation introduces no active API/UI/schema changes.
Training, test evaluation, migrations and runtime product acceptance were not run.
