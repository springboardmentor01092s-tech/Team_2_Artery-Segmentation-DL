# Role section and dashboard mapping

Source: supplied `CoroVision_AI_Role_Based_Sections_and_Dashboards_Spec.md`,
reviewed 16 October 2026. Status labels refer to the application, not just document
coverage. This increment changes navigation/UI only; no new worker, permissions,
datasets, model metrics or training runs were created.

## Role by role section matrix

The application uses internal `SidebarView` identifiers, not separate URL routes.
HTTP resources still use protected `/api` endpoints. A deep-link router is not
claimed. `canOpenSection` centrally filters navigation and resets unauthorized
active sections; backend authorization remains independent and authoritative.

| Role | Spec section | View or implementation | Status and limits |
|---|---|---|---|
| Researcher | Research Overview | overview / OverviewPanel | Partial: existing layout and data preserved; full metric provenance/click-through still pending |
| Researcher | Research Cases | cases | Implemented core list/detail; broader asset/version lifecycle partial |
| Researcher | Data & Uploads | uploads | New direct entry into existing case preparation; no persistent volume library/quarantine service |
| Researcher | Analysis & Explainability | analysis | Partial: saved 2D outputs/history; synchronous inference, not durable jobs |
| Researcher | Model Evaluation | models | Partial: existing recorded registry/evaluation, not all task metrics or immutable evaluation service |
| Researcher | Datasets & EDA | No separate view | Missing integrated registry; local audit files/scripts are not a live registry |
| Researcher | Reports & Exports | reports | Partial: existing case reports/export; full generation queue/history incomplete |
| Clinician | Clinical Overview | overview | Existing role-aware OverviewPanel, renamed navigation; complete clinical workload cards partial |
| Clinician | Research Cases | cases | Existing assigned/owned case access, no new patient identifiers |
| Clinician | Image Review | analysis | Existing image/results viewer; reference/3D/version-specific controls partial |
| Clinician | Analysis Results | Inside analysis and case history | Partial; not a duplicate standalone sidebar page |
| Clinician | Severity Review | reviews / ReviewQueue | New searchable actual review-authorized case list; opens existing human review form |
| Clinician | Reports & Exports | reports, labelled Review Reports | Existing authorized review-report path; no new automated diagnosis |
| ML engineer | ML Overview | overview / RoleWorkspace | Partial capability overview, not live experiments/compute telemetry |
| ML engineer | Model Evaluation and Model Registry | models | Partial shared read-only registry/evaluation; activation/approval not granted |
| ML engineer | Datasets, EDA, Experiments, Error Analysis, Diagnostics, Exports | Not separately connected | Missing integrated services; training remains paused and is intended for another laptop |
| Admin | Administration Overview | overview / RoleWorkspace | Governance entry points, not measured worker/storage dashboard |
| Admin | User Management | admin / AdminPanel users | New focused section over existing account/access-request APIs; invitations/revoke-other-session tools incomplete |
| Admin | Roles & Permissions | permissions / AdminPanel permissions | New separate grants and matrix view; no new privileges conferred |
| Admin | Workspace & Case Access | access / AdminPanel access | Partial: existing recoverable trash plus scope explanation; no institution membership/ownership correction service |
| Admin | Model Registry & Approvals | models, labelled Model Registry | Partial existing registry/research activation; approvals deliberately not claimed |
| Admin | Audit Logs | audit / AdminPanel audit | New focused filterable loaded audit window; not complete paginated historical archive |
| Admin | Dataset Registry, Jobs, Configuration, Storage, Security Health | Not separately connected | Missing full services/telemetry; no empty clickable pages posing as working modules |
| All applicable roles | Notifications | Existing header bell | Implemented existing notification path; no duplicate dashboard column added |
| All roles | Profile & Settings | account | Existing profile/security/preferences; Appearance stays at bottom |
| Viewer and technician | Existing restricted workspaces | Preserved | Viewer remains read-only; technician intake allowed, review and ML controls denied |

## Dashboard card definitions and remaining gaps

Research Overview was intentionally not rewritten. Definitions below document
what its current code actually calculates, not every requested target behaviour.
Scope is authorized non-deleted cases returned by `/api/cases`; there is no
workspace/time-window selector in this increment.

| Card or panel | Source and counting rule | Unit and click destination |
|---|---|---|
| Total cases | `cases.length` from authorized case list | Cases; card is not currently clickable; View cases opens cases |
| Images uploaded | Sum of stored `images.length` for authorized cases | Stored 2D image variants, not people/volumes/raw unique sources; card not clickable; uploads is direct sidebar destination |
| Cases analyzed | `/dashboard/analytics` latest AnalysisEvent per case; legacy frontend status fallback if unavailable | Cases with recorded history; card not clickable; cases/history supports inspection |
| Recorded model runs | Count of accessible AnalysisEvents | Historical analysis events; not running jobs |
| Pending review | Client case status analyzed and no latest review | Cases, not analysis-job count; no card filter click-through; reviews list uses pending_review workflow and only review-authorized cases |
| Model-flagged region | Analytics latest event per case has positive stenosis pixel count | Cases under latest saved event; not any historical positive result or a disease diagnosis |
| No model region flagged | Analyzed case count minus latest-event flagged cases | Cases; no claim of normality |
| Clinician severity | Latest review per accessible case, explicit recorded severity | Reviewed cases; missing/empty severity maps to unspecified, missing review does not map to none; explicit empty-state improvement pending |
| Validation panel | `validation_summary()` reads selected comparison report or applicable training report artefact | Task-specific recorded Dice/count; full immutable run/aggregation/exclusion provenance remains partial |
| Processing status | Count by stored case.processing_status | Cases, not live worker jobs |
| Recent analyses | Latest eight accessible saved events | Event rows open supporting case |

Keep dashboard validation values separate from the PRD's reported two-sample
inference numbers. No numeric metric was copied into UI code in this increment.
Source dataset warning assertions remain subject to the existing PRD evidence
reconciliation; no unverified quarantine list was created.

## New section behaviour

- Data & Uploads opens Assets & preparation for the selected accessible case.
  Owner/edit scope and upload permission still control the actual form.
- Severity Review filters only cases whose API response grants `can_review`.
  Pending means stored `workflow_status == pending_review`. Other filters use
  the actual latest decision. No overdue/clinical-priority score is fabricated.
- Review rows show current recorded severity and review time, then open the
  existing case review form. The queue does not implement a new result-version
  assignment/decision lifecycle or automated severity grading.
- Admin sections request only their relevant datasets: users for users/permissions,
  trash for case access, audit for audit. Search is over loaded records and audit
  defaults to ten with show-all-loaded. Backend errors have a retry action and
  loading/empty states are explicit.
- Unknown sections are denied. Admin case/upload/analysis/export navigation still
  needs its existing explicit operational grants plus independent resource scope.

## Verification

`node --test tests/navigation.test.mjs` from frontend: 4 tests passed, covering
viewer/ML isolation, professional sections, admin grants and unknown-section deny.
`npm run build` from frontend: TypeScript/Vite passed; existing chunk-size advisory.
11 selected backend tests passed across role policy, operational grants, RBAC,
dashboard/model registry and shared workflow. Existing short test JWT-key warnings
remain. These isolated tests do not train or run real GPU inference.

Browser checked existing signed-in researcher navigation, unchanged Research
Overview values and direct Data & Uploads with protected read-only assignment.
Full clinician/admin browser walkthrough, mobile and assistive-technology review
remain pending; frontend policy tests are not claimed as those walkthroughs.

Changed source: `permissions.ts`, `macos-sidebar.tsx`, `App.tsx`, `AdminPanel.tsx`,
new `ReviewQueue.tsx` and `tests/navigation.test.mjs`. No backend restart/schema
upgrade was needed for this increment.
