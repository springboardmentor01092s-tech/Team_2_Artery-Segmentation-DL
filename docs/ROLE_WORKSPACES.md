# CoroVision AI role workspaces

The five workflow groups in the project plan map to seven stored roles because doctors and clinicians, and medical researchers and ML engineers, have distinct workspaces. All users share one React application. The sidebar labels and dashboard content change by role; FastAPI checks the actual role and case assignment on every protected action.

| User | Main navigation | Current actions | Boundary |
| --- | --- | --- | --- |
| Administrator | Dashboard, Case Inventory, AI Analysis, Model Status, Reports, Administration | Manage roles and account status, read system audit events, assign case access, view model status | Cannot submit clinical reviews without a doctor/clinician role; no model deployment control exists |
| Doctor / Clinical Reviewer | Dashboard, My Cases & Reviews, AI Analysis, Reports | Inspect assigned cases, run inference, record a clinical decision when assigned `review` or `edit` access, export an accessible case | Cannot administer users; a `read` assignment does not permit review |
| Medical Researcher | Dashboard, Research Cases, AI Analysis, Model Evaluation, Reports | Create de-identified cases, upload, run inference, inspect validation results, export accessible cases | Cannot submit clinical reviews or administer users |
| ML Engineer | Dashboard, Model Evaluation | Inspect available model version and saved validation Dice/sample counts | No case access or training/deployment UI from this role alone |
| Technician / Data Operator | Dashboard, Case Intake, Image Inspection, Reports | Create cases, upload images, check preprocessing, run inference on accessible cases | Cannot record clinical decisions or export reports |
| Viewer / Student | Dashboard, Assigned Cases, AI Results, Reports | Read assigned cases, previews, overlays and summaries | Cannot create, upload, run inference, review, edit, or export |

## Case permissions

- A case owner can edit, upload, and move the case to Trash. An administrator can also move a case to Trash or restore it. A case assignee needs `edit` access for editing and uploading; assignment alone does not permit deletion.
- A doctor/clinician can record a review on an owned case or an assigned case with `review` or `edit` access. A `read` assignment permits inspection only.
- Inference and exports require both a permitted role and access to the case. The API remains authoritative if a browser is modified or an old page is open.
- Administrators can inspect cases for platform management; the administrator role does not carry clinical review authority.
- Report approval requires an administrator to grant a doctor or clinician explicit `can_approve_reports` permission. The approver must have case review access and cannot approve a report they submitted.

## Shared case workflow

1. A technician or another case creator registers a pseudonymous case. The case begins in `draft`.
2. An authorized user uploads an image. Validation and preprocessing record a separate `processing_status`; accepted images move the case to `ready_for_analysis`. Failed validation records `validation_failed` and a notification so the intake user can correct it.
3. A researcher or another authorized case user runs AI analysis. The case moves to `pending_review`. The analysis remains a research prediction until a clinician assesses it.
4. A doctor or clinician with review access records a clinical review. A completed review moves the case to `reviewed`; a rejected or follow-up review moves it to `changes_requested`.
5. A reviewer submits a versioned report snapshot for approval. A separately authorized doctor or clinician approves it or requests changes. Approval marks the report `approved` and case `complete`; changes return the case to `changes_requested`.
6. The viewer can inspect assigned case results. Reports show their approval state and version. Case notes, notifications, dashboard tasks, and audit events record each handoff. Active case lists hide deleted cases; administrators can restore them from Trash.

## Local demo collaboration

With `CV_LOCAL_DEMO_SHARING=1` in the local backend `.env`, cases created by the seeded demo accounts are shared automatically with the seeded team. Doctors, clinicians, and technicians receive `edit` access; researchers and viewers receive `read` access. The administrator retains platform access, while the ML engineer role still has no case access. This applies only to the named demo users and de-identified prototype data. Remove the setting before deployment. `python3 sync_demo_cases.py` from `backend` adds missing grants to older demo cases without replacing existing assignments.

Open browser sessions refresh authorized cases about every 2.5 seconds while visible and immediately on focus. New images, analysis runs, metadata edits, and clinical reviews appear in the case list and detail views. An open metadata form preserves unsaved typing; if another user changes that case, saving pauses until the editor loads the newer version. Separate users never gain access merely because another session has a case open.

## Planned work, not active controls

The source document also proposes a dataset catalog, training experiments, model comparisons, a model registry, deployment settings, and system storage monitoring. Those need matching data models, jobs, and API authorization before they become interactive sections. The current model evaluation page shows only recorded validation results; it does not fabricate additional metrics or comparison runs.
