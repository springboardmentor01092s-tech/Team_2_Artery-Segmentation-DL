# PRD application changes

## Implemented foundation increment

- Case creation now records modality, anatomy, intended research task and source
  dataset/release. Metadata editing includes source case/study reference.
- Supported configurations: coronary XCA segmentation/localization research;
  CT/CTA/MRA volume preparation for coronary, aortic, cerebral or hepatic anatomy.
  These are preparation configurations, not newly connected inference models.
- Server validation rejects incompatible configurations. Modality/anatomy/task
  cannot change once 2D images exist; create a separate case instead so saved
  outputs are not reinterpreted under different metadata.
- Existing synchronous XCA inference still produces its established dual-model
  output. Task is recorded as research intent; this increment does not implement
  independent per-task model selection or a durable worker queue.
- Clinical history/risk factors/clinical notes are default-disabled and require
  explicit opt-in for de-identified research context. Disabling editing preserves
  historical values, not a purge or an access-revocation mechanism. Case access
  remains the server authority. Opt-in is not consent or institutional approval.
- Cases are separated into Overview & access, Assets & preparation, Reviews &
  notes, and Analysis history, with links to existing analysis and report tools.
- Sidebar filters include modality and research task alongside existing status,
  search, sort and pagination. New-case controls use progressive disclosure.
- Reviews identify research-use limitations and expose recorded review history.
  This does not add a four-decision result-version review assignment service.
- API validation arrays now produce readable field-level error messages.

## Storage and compatibility

Four additive case columns were added to the local SQLite upgrade map. Existing
XCA rows retain combined research intent; existing CT/CTA/MRA/MRI rows are marked
volume preparation. Sources remain unknown unless an operator records them.
The new upgrade is repeatable and tested against a legacy fixture. PostgreSQL
upgrades still require explicit deployment migrations; SQLite helper is not a
cross-database migration system.

Before restarting the verified local backend, a SQLite backup was saved at
`output/backups/artery_before_prd_case_configuration_20261016.db`. Original
images, annotations, dataset partitions, checkpoints and account grants were not
modified. Training remains paused. The existing frontend session remains usable.

## Verification and limitations

41 selected isolated API tests passed across case configuration/migration,
preprocessing, RBAC/authentication, operational grants, shared workflow and volume
preparation. A legacy test now explicitly opts into its legitimate clinical-data
fixture. Initial regressions were corrected before the passing run.

Browser checks confirmed the revised sections and read-only assignment behaviour;
the existing preview renders without new inference. New model training, full
mobile/screen-reader testing, persistent jobs, a database dataset/EDA registry,
model submission/approval, complete PDF generation and validated severity remain
outside this completed increment. Test JWT-key warnings and the frontend
bundle-size advisory remain. No highest-metric or clinical-readiness claim is made.

Changed source: backend `case_contract.py`, `main.py`, `models.py`, `migrations.py`;
frontend `App.tsx`, `CaseDetails.tsx`, `caseConfiguration.ts`, `caseTypes.ts`,
`api.ts`, `theme-consistency.css`; two backend test files.
