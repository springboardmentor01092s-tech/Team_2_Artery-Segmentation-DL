# CoroVision AI frontend workflow

See the [role section mapping](ROLE_SECTIONS_ROUTE_MATRIX_2026-10-16.md) for the
current sidebar identifiers, feature statuses and dashboard counting definitions.
Researcher Data & Uploads, clinician Severity Review, and separate administrative
Users/Permissions/Case Access/Audit sections reuse protected existing workflows.

The application follows: sign in → select or create a de-identified case → upload an image → run research inference → inspect the original/processed image and overlay → review or export results.

## Navigation

| Section | Current use |
| --- | --- |
| Dashboard | Role-specific entry point, accessible case counts, recent studies, and quick actions. |
| Cases | Search, status filter, sort, paginate, edit permitted metadata, assign case access, upload multiple images, and inspect preprocessing. |
| AI Analysis | Original/processed/overlay viewer, zoom and pan, overlay opacity, inference action, findings, and run history. |
| Model Evaluation | Deployed model status and recorded validation Dice with sample counts. |
| Reports | AI-generated summary and human review, when recorded. Authorized users can export JSON/CSV or print to PDF. |
| Profile & security | Account settings, password, sessions, and user audit history. |
| Administration | Role and account status management plus administrator audit history. |

The sidebar follows server permissions. Researchers, doctors/clinicians, technicians, viewers, ML engineers, and administrators see the sections available to their roles. The API remains the authority for every case and export action; menu visibility does not grant access.

See [Role workspaces](ROLE_WORKSPACES.md) for each user's visible sections, active actions, case access rules, and planned features.

## Image handling

The upload workflow distinguishes new-case inference from the ARCADE research dataset. Inference accepts supported raster, DICOM, or scanned-PDF images up to 50 MB each. The Standard profile is conservative; researchers can opt into median denoising and clipped autocontrast separately. Exact duplicate files within a case are skipped. Failed validations remain queued with an error message, and a progress indicator reports each file. DICOM frame and PDF page selection, ROI cropping, reproducible processing records, warnings, and spacing metadata appear in the case view. Dataset images remain paired with their task-specific COCO labels and official splits through the dedicated dataset pipeline.

## What the model currently supports

The deployed baseline predicts artery and suspected stenosis masks from X-ray coronary angiography. The workbench displays the stored color overlay and mask pixel counts. The evaluation page displays only metrics present in the saved validation report. Clinician review is recorded separately from AI output.

The current model does **not** supply reliable vessel segment labels, lesion coordinates, diameter or narrowing measurements, calibrated confidence, Grad-CAM, or a validated severity grade. IoU, precision/recall/F1, ROC, test-set metrics, and U-Net architecture comparisons are not shown until those experiments produce verified results. Model promotion and rollback controls are not implemented.

PDF export uses the browser print dialog's **Save as PDF** option. JSON and CSV are direct downloads. All three first call the authorized case export endpoint so the action is recorded in the audit trail.
# Current specification

The [consolidated PRD](CoroVision_AI_Comprehensive_PRD_Infosys_Springboard_Team_2.md)
defines the target role-aware navigation and end-to-end workflows. The
[implementation checklist](PRD_IMPLEMENTATION_AND_ACCEPTANCE.md) distinguishes
implemented shared tools from proposed module pages and persistent jobs. Older
workflow notes below are historical and do not establish completion of new targets.

