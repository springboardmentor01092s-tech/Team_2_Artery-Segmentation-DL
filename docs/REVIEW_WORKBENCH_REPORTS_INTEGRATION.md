# Image Review → Severity Review → Reports

## Audit

The existing React application shares case/image selection in App.tsx. Uploads persist Image records; persistent AnalysisJob workers create immutable AnalysisEvent records and artifact files. Image Review already supports zoom/pan, history, saved overlays and derived geometry. No new predictions or demonstration metrics are needed.

Before this change ClinicalReview was case-only, so its decision could not identify the image/run actually reviewed. ReportsPage assembled transient browser exports and used print for PDF. ReportRevision already snapshots a separate clinical approval workflow; that workflow must remain intact.

## Changes

- Nullable image/run references on human reviews preserve legacy case-only history without inventing an evidence association.
- Dedicated evidence review workspace reuses the shared viewer, selected image and immutable run history. Human assessments never derive automatically from pixel masks.
- ResearchReport stores immutable, versioned research snapshots, separately from ReportRevision approval records. Backend validates case/image/run identity and operational export permission on create/list/read/export. A research snapshot is not an approved clinical report.
- Every snapshot includes source identifiers, selected saved result, exact processing record, selected-run human review history, generation time and non-removable limitations. Optional contents affect presentation only; safety/provenance remain mandatory.
- JSON, tabular CSV and downloadable PDF are generated from the saved snapshot, never from mutable frontend state. Prior snapshots remain readable after reruns/reviews.
- Viewer layers are enabled only after successful artifact fetch; candidates focus the image using saved prepared coordinates. Unsupported 3D and uncomputed attention layers remain unavailable.

## Acceptance

Test run-bound review persistence and legacy compatibility; foreign case/image/run rejection; research snapshot immutability after new runs and reviews; JSON/CSV/PDF values matching the snapshot; missing measurement semantics; unauthorized read/export; missing artifact feedback; responsive viewer and keyboard-accessible controls. Existing real public-image inference receipt is retained; report integration tests use deterministic isolated fixtures and are not a model-performance evaluation.

## Verified results (25 October 2026)

- Full backend: `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests -q` - **88 passed, 2 skipped** (opt-in installed-weight/public-fixture tests), 53.71 seconds. Existing Starlette/Pillow deprecation and test-only JWT-key-length warnings remain.
- Frontend: production TypeScript/Vite build passed; **14 Node tests passed**. Non-failing existing bundle-size warning remains.
- Dedicated tests cover saved-run review binding, required insufficient-evidence notes, case/image/run mismatch rejection, two different uploaded images, missing numeric values versus genuine zero, CSV formula protection, unauthorized snapshot read/export, missing overlay PDF fallback, repeatable migration, immutable earlier snapshots and rerun identities.
- Existing clinical report submission/independent approval tests still pass. Research snapshots do not grant approval or replace that workflow.
- Browser: reused public ARCADE case `PUBLIC-ARCADE-CHECK-5ddc8f`; verified Original, mask/overlay availability, disabled Attention/Grad-CAM, selected-run identity, candidate-focus zoom, clinician-specific assessment controls and saved research report preview. Added one explicitly labeled insufficient-evidence **workflow-test** review, not a medical opinion.
- Real installed-checkpoint rerun completed: event `a67e848f-1a07-4caa-a0ed-db2407ab8e47`, job `0ff936c3-3a60-419e-ac4c-d9f65f2ac4ab`. Three historical events remain available. Existing public upload was reused rather than uploading the same image again.
- Earlier research report `db480980-74bc-487f-aeb1-90fbbac1e8cc` still references event `88554854-018a-4737-9f68-a392521756bc` and its recorded review. Its JSON export matches the immutable snapshot exactly; CSV run ID/pixel values match; PDF download is valid and was rendered for visual inspection. See `reports/review_report_integration_receipt.json` for export hashes.
- Responsive CSS stacks viewer/results and report-builder panels at smaller widths. Desktop browser was visually inspected; a real small-device viewport and independent dark-mode visual check have not been completed in this session.

## Changed files for this increment

Backend: `models.py`, `migrations.py`, `main.py`, new `research_reporting.py`, `requirements.txt`, new `tests/test_review_reporting.py`.

Frontend: `App.tsx`, `AnalysisWorkbench.tsx`, `ReportsPage.tsx`, `ReviewQueue.tsx`, `caseTypes.ts`, `styles.css`, new `ReviewAssessment.tsx`, `reviewEvidence.ts`, `tests/review-evidence.test.mjs`.

Verification: `scripts/verify_review_report_workflow.py`, `reports/review_report_integration_receipt.json`, this document. Existing unrelated changes were preserved; no Git push was performed.

## Remaining boundaries

No new model approval, training, clinical grade, urgency classification or candidate-to-vessel association was introduced. 3D slice/inference controls remain unavailable because a supported volumetric inference workflow is not connected. Attention/Grad-CAM is enabled only if a saved artifact can be fetched. Execution duration is calculated from the selected run's persisted job timestamps only when its result ID matches; legacy jobs show unavailable. Research snapshots preserve references to immutable artifact files, not a separate duplicate of each image. Old case-only reviews remain unbound and are not silently attributed to a selected run. JSON retains full evidence; optional PDF/preview sections configure presentation, not redaction.
