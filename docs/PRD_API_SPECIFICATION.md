# CoroVision API reconciliation

16 October 2026. Target requirements are in the [consolidated PRD](CoroVision_AI_Comprehensive_PRD_Infosys_Springboard_Team_2.md).
All paths below use `/api`. Existing methods must not be renamed merely to match
illustrative paths in the pasted specification. Source: `backend/app/main.py`,
`auth_ext.py`, current frontend callers. Swagger describes contracts, not proof
of scientific or production readiness.

## Existing contract surface

| Function | Existing route examples | Qualification |
|---|---|---|
| Accounts | POST /auth/register; POST /auth/login; GET/PATCH /auth/me | Register uses email/password/display_name/optional username; grants viewer. Login uses identifier or email/password/remember. Bearer response |
| Sessions | GET /auth/sessions; POST /auth/logout; POST /auth/logout-all; POST /auth/change-password | Revocable sessions; password reset/provider routes live in auth extension |
| Workspace requests | GET/POST /auth/access-requests; GET /admin/access-requests; POST /admin/access-requests/{id}/decision | Manual professional eligibility; no self-approval |
| Users | GET /admin/users; POST /admin/users/{id}/role; POST /admin/users/{id}/status | Restricted audited actions; current status method is POST, not suggested PATCH |
| Operational grants | POST /admin/users/{id}/operational-grant | Role maximum and no-self-grant checks; never bypasses case scope |
| Cases | GET/POST /cases; GET/PATCH/DELETE /cases/{id} | Recoverable deletion; validated task/source and modality/anatomy configuration; CT/CTA/MRA preparation only; see foundation increment |
| Sharing | POST /cases/{id}/access | Explicit scoped assignment, not institution-wide membership |
| Images | POST /cases/{id}/images; GET /images/{id}/source; GET /images/{id}/preview | Multipart intake; original plus derived PNG; protected retrieval |
| Volumes | POST /cases/{id}/volumes/prepare | Separate temporary preparation/export, not persistent 3D asset listing |
| Inference | POST /images/{id}/analyze | Synchronous XCA inference, not queue submission |
| History | GET /images/{id}/analyses; GET /cases/{id}/analyses | Persisted completed analysis/event records |
| Comparison | GET /images/{id}/analysis/compare | Existing two-run comparison is not full protocol-aware benchmark comparison |
| Results | GET /images/{id}/analysis; protected overlay/map endpoints | Source-case access still required |
| Reviews | POST /cases/{id}/review; GET /cases/{id}/reviews | Clinical review schema is not automatically the new four-decision result-review lifecycle |
| Reports | POST /cases/{id}/reports/submit; POST /cases/{id}/reports/{version}/decision; GET /cases/{id}/reports/{version} | Existing research report revisions/decisions; complete PDF pipeline needs verification/implementation |
| Export | GET /cases/{id}/export | Permission plus resource checks; do not infer every requested file format |
| Models | GET /analysis/models; POST /analysis/models/activate | Read-scoped registry; admin research-checkpoint activation, not clinical approval |
| Activity | GET /notifications; POST /notifications/{id}/read; GET /dashboard/analytics | Real scoped data; not complete asynchronous job observability |
| Audit | GET /auth/audit; GET /admin/audit | Own versus administrative scope |

## Upload request compatibility

Keep multipart `profile=standard|research` and
`standard_pipeline=baseline|denoise|contrast|balanced`. UI Standard maps to
baseline. Preserve ROI/frame/PDF-page options and restricted research flags.
Response processing record includes version, source/settings identity, operations,
geometry and warnings. A repeated source with distinct settings is an intentional
variant; identical source/settings is rejected. Current pre-check is not atomic
idempotency across concurrent requests.

## Proposed additions not implemented by this consolidation

| Proposed surface | Minimum contract |
|---|---|
| GET /auth/me/permissions | Optional normalized projection of effective permissions already in /auth/me; no duplicate policy resolver |
| /datasets and /datasets/{id}/manifest, /eda, /findings | Versioned, authorized records and artefact references; evidence and licence/grouping status |
| /cases/{id}/assets and /assets/{id}/validation | Typed sources/references/derived/predictions; quarantine and geometry; map existing images without breaking IDs |
| POST /cases/{id}/analysis-jobs | Asset/task/model/config version and idempotency key; validate scope/compatibility; persist before enqueue; return 202 with job ID |
| GET /analysis-jobs/{id} | State, timestamps, attempt and measured progress; safe error; survive refresh |
| POST /analysis-jobs/{id}/retry | Authorized retryable failure only; new attempt, preserved failure; idempotent submission |
| GET /analysis-results/{id} | Saved outputs, reference provenance, metric definitions, protocol, sample counts, units and limitations |
| /reviews and /reviews/{id}/decisions | Assignment and result version, explicit decision enum, append-only history; approval permission separate |
| /model-versions and approval decisions | Immutable artefact/config IDs and scoped approval; cannot self-approve implicitly |
| POST /reports and GET /reports/{id}/download | Frozen authorized result/review snapshot, generation status and PDF; export audit |
| /experiments and /system/health | Scoped experiment provenance; safe measured component health, never secrets |

Each addition needs Pydantic schemas, pagination where applicable, access/error
contracts, transactions and tests before UI enablement. Prefer stable opaque IDs
and protected artefact routes over returning internal paths. Use explicit 401,
403 or non-disclosing 404, 409 conflict, 422 invalid input and 503 unavailable
behaviour consistently with existing policy. A 202 does not mean completion.

## Verification obligations

Test missing/expired/revoked tokens, non-active accounts, stale role tokens,
cross-case access, reference/prediction confusion, unsupported tasks, malformed
files, duplicate submission races, worker failure/restart, retry history and
download authorization. Do not execute real GPU inference or training in contract
tests; use isolated fixtures/mocks and label resulting test outputs accordingly.
