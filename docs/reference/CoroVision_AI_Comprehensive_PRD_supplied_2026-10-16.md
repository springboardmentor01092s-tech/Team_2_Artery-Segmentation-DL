# COROVISION AI
## Comprehensive Product Requirements Document (PRD)

**Project:** Artery Segmentation and Stenosis Detection Using Advanced Deep Learning Techniques  
**Program:** Infosys Springboard  
**Team:** Team 2  
**Document status:** Consolidated requirements draft for team review and implementation planning  
**Date:** 16 October 2026  
**Intended use:** Research and educational prototype; not a standalone clinical diagnostic system

### Team Members
- Mayuri Mukunda Jamdar
- Kedar Muley
- Kolli Deepika
- Anupati Goutham Teja
- Harshitha Sg
- Rishika Nakirtha
- Laveen Kumar Tamarani
- Lingareddy Dhanush Kumar Reddy

---

## Document Purpose and Requirement Status

This PRD consolidates the uploaded 28-page project specification, the later role/dashboard/case-management requirements discussed in this conversation, the supplied dataset EDA, and the reported sample-inference results.

It defines **what the product should do** and how success should be checked. It does not claim that every described module is already implemented. Codex and the team must audit the current repository, mark each requirement as implemented, partial, missing, or blocked, and avoid rewriting working functionality unnecessarily.

Requirement labels:
- **P0 — Foundation:** needed to safely run a coherent end-to-end research workflow.
- **P1 — Core analysis:** required for the first useful research demonstration.
- **P2 — Advanced:** add after the earlier phases are stable and evaluated.
- **Proposed:** a suggested design or stack choice that the team must confirm.

## 1. Executive Summary

CoroVision AI is a research-support web application intended to organize vascular imaging cases and provide workflows for artery segmentation, vessel structure analysis, stenosis detection and localization, carefully qualified severity estimation, visualization, model evaluation, and report generation.

The original project specification proposes support for medical image sources such as CT angiography (CTA), coronary angiography, and other suitable vascular datasets. Because these modalities and anatomical regions differ, the system must use task-specific pipelines selected by **modality + anatomy + task + compatible model version**. It must not treat all vascular datasets as interchangeable.

The platform is expected to provide:
- Secure registration/login, JWT-based authentication, session management, profiles, role-based access, and audit logging.
- Structured research subject and case management, with image/study assets and analysis history.
- Medical image validation and reproducible preprocessing.
- Artery segmentation and vessel visualization.
- Vessel centerline, branching, continuity, and measurement analysis where supported.
- Stenosis candidate detection/localization and severity analysis only when appropriate labels and defensible measurements are available.
- Explainability visualizations, model training/evaluation, model version management, and result comparison.
- Researcher/clinician dashboards, reports, notifications, and an administrative workspace.
- Testing, containerization, deployment, and operational monitoring.

The current sample-run observation reports segmentation Dice 77.36%, precision 92.30%, recall 66.58% on a reported ARCADE image/result; basic mask area, connected components, and approximate pixel width were saved; and a stenosis example's annotated lesion was missed at score cutoff 0.05. These are preliminary observations, not verified dataset-wide performance. The product must make that distinction explicit.

## 2. Product Vision, Problem, Goals, and Non-Goals

### 2.1 Vision
Provide a transparent, reproducible research workspace that reduces manual steps in vascular-image preparation and analysis while preserving traceability, data quality, and honest representation of model limitations.

### 2.2 Problem statement
Researchers and medical imaging specialists work with different image modalities, study structures, annotation formats, splits, models, and metrics. Without a structured workflow, it is difficult to ensure that images and annotations align, that cases are access-controlled, that model versions are comparable, or that reported performance is valid.

CoroVision AI should make the workflow traceable from uploaded source asset to validation, preprocessing, model inference, saved results, review, and exported report.

### 2.3 Product goals
1. Authenticate users and enforce the correct permissions on every protected backend operation.
2. Provide four role-specific workspaces: Radiologist/Clinician, Medical Researcher, Data Scientist/ML Engineer, and Administrator.
3. Manage de-identified research subjects, cases, images/studies, and case history.
4. Validate uploads and prepare medical images without silently losing geometry or annotation alignment.
5. Support separate model pipelines for 2D angiography and 3D CT/CTA, and for different anatomical/task labels.
6. Provide segmentation masks, vessel structure outputs, and stenosis candidates where models and labels support them.
7. Show reference annotations and model predictions distinctly.
8. Track model/preprocessing versions, jobs, experiments, reviews, and exports.
9. Report task-appropriate evaluation metrics and identify data leakage, small-sample, label, and geometry limitations.
10. Create useful reports with provenance, visualizations, measurements, and research-use limitations.
11. Support a staged path to tests, Docker-based packaging, and cloud deployment.

### 2.4 Non-goals and safety boundaries
- Replacing clinical judgment or autonomously diagnosing patients.
- Claiming clinical validation or regulatory approval without independent evidence.
- Treating a model score or heatmap as proof of correct clinical reasoning.
- Treating an unannotated or zero-polygon image as a healthy case by default.
- Reporting physical diameter, percentage narrowing, blood flow, or vessel capacity from uncalibrated pixel measurements.
- Reporting sample metrics as overall model performance.
- Mixing unrelated anatomy, modalities, and annotation semantics into one universal model.
- Treating pseudo-labels as equal to expert-verified ground truth.
- Using overlapping datasets as independent external test cohorts without an explicit exclusion protocol.

## 3. Scope and User Groups

### 3.1 In-scope modules
1. User authentication and role-based access.
2. Research subject/patient and case management.
3. Medical image upload and preprocessing.
4. Artery segmentation.
5. Vessel structure and centerline analysis.
6. Stenosis detection and localization.
7. Stenosis severity assessment.
8. Advanced model experimentation and model management.
9. Explainability and result visualization.
10. Training and evaluation.
11. Segmentation evaluation.
12. Stenosis detection evaluation.
13. Clinician/researcher dashboards and image analysis workspace.
14. Report generation and PDF/JSON/CSV export.
15. Notifications and alerts.
16. Model versioning and dataset version tracking.
17. Frontend/backend integration, testing, Docker packaging, deployment, logging, and monitoring.

### 3.2 Human roles
- Radiologist / Clinician
- Medical Researcher
- Data Scientist / ML Engineer
- Administrator

A background analysis worker is a restricted service identity, not a human role. A reviewer/supervisor workflow may be enabled through a scoped review permission assigned to a clinician or researcher; avoid creating a fifth full role unless the team decides it is needed.

## 4. Roles and Permission Model

### 4.1 Radiologist / Clinician
**Purpose:** Review authorized imaging cases and interpret research outputs with appropriate caution.

Application sections:
- Clinician Dashboard.
- Authorized Case List and Case Details.
- Image/Study Viewer.
- Segmentation and Stenosis Review.
- Measurement Review.
- Previous Analysis Comparison.
- Clinical/Research Notes, as authorized.
- Reports and Export.
- Alerts and Notifications.
- Profile and Session Settings.

Expected actions:
- View assigned/authorized cases and image metadata.
- View original and preprocessed images.
- Toggle predicted masks, reference labels, centerlines, stenosis candidates, and explanation overlays.
- Inspect detection score, thresholds, model version, and supported measurements.
- Compare older and newer analyses for the same compatible case/task.
- Record review comments and a decision such as accepted for research review, changes requested, or rejected.
- Generate or export permitted reports.

Restrictions:
- Must not treat the application as a standalone diagnosis.
- Cannot silently change model weights, dataset splits, reference labels, or historical evaluation data.
- Clinical information fields must remain optional and protected for this student/research prototype.
- No model output should be described as a confirmed diagnosis.

### 4.2 Medical Researcher
**Purpose:** Organize research cases, run permitted analysis workflows, review results, and prepare reproducible research artifacts.

Application sections:
- Researcher Dashboard.
- Cases.
- Data & Uploads.
- Preprocessing History.
- Analysis Workspace.
- Evaluation.
- Dataset Registry and EDA.
- Reports.
- Notifications.
- Profile and Settings.

Expected actions:
- Create cases using research identifiers.
- Upload de-identified image/study assets and reference masks where permitted.
- Run supported, compatible analysis jobs.
- Reopen prior results.
- Compare versions and view evaluation metadata.
- Annotate research notes and request review.
- Generate reports.
- Inspect EDA warnings and respond to data-quality findings.

Restrictions:
- Cannot grant self additional permissions.
- Cannot access cases without authorization.
- Cannot designate predictions as verified ground truth without an approved review process.
- Cannot tune a final test set through the ordinary evaluation workflow.

### 4.3 Data Scientist / ML Engineer
**Purpose:** Manage dataset preparation, model training, evaluation, experiments, and model versions.

Application sections:
- ML Dashboard.
- Dataset Registry.
- EDA & Data Quality.
- Experiment Manager.
- Training Runs.
- Model Registry.
- Evaluation Reports.
- Error Analysis Gallery.
- Inference Diagnostics.
- Deployment/Compatibility Status.
- Profile and Notifications.

Expected actions:
- Inspect manifests, annotation semantics, split membership, image dimensions, foreground distribution, and known duplicates.
- Configure supported training experiments.
- Record parameters, random seeds where practical, code/environment versions, and checkpoint hashes.
- Run validation and final evaluation with split protections.
- Compare model versions using task-appropriate metrics.
- Inspect false-positive/false-negative examples and threshold effects.
- Register model artifacts and submit versions for approval.
- Debug preprocessing, output decoding, class mapping, and coordinate alignment.

Restrictions:
- Cannot claim one model applies to all modalities/tasks.
- Cannot approve a model outside the actor's permission scope.
- Must keep patient/study groups and known duplicates from leaking across splits where identifiers permit.
- Must not fabricate labels, sample counts, or model results.

### 4.4 Administrator
**Purpose:** Manage accounts, permissions, application configuration, model/dataset registries, auditability, and system operations.

Application sections:
- Administration Dashboard.
- User Management.
- Roles & Permissions.
- Workspace/Case Access Administration.
- Dataset Registry Administration.
- Model Registry and Approvals.
- Background Jobs.
- System Configuration.
- Storage/Retention.
- Audit Logs.
- Security and System Health.

Expected actions:
- Invite, activate, deactivate, and assign roles to users.
- Revoke sessions or tokens according to the authentication architecture.
- Manage allowed formats, upload limits, and approved task/model compatibility.
- Monitor job failures, worker status, storage, and system health.
- Review security and export audit logs.
- Manage model approvals, deprecation, and rollback where supported.
- Manage retention and archiving policies.

Restrictions:
- Administrator status must not automatically grant unlimited access to medical image content; content access should be separately permissioned.
- Destructive actions must require confirmation and be audited.
- Secrets must not be displayed in administration UI.
- Historical analysis/review records must not be silently overwritten.

### 4.5 Service identity
Background workers run preprocessing, inference, evaluation, and report jobs. Give them only scoped access to the assets, model artifacts, and state transitions required by their jobs. Workers must not assign roles or bypass authorization policies.

### 4.6 Permission matrix (initial proposal)

| Capability | Clinician | Researcher | Data Scientist / ML Engineer | Administrator |
|---|---|---|---|---|
| View authorized cases | Yes | Yes | Scoped | Scoped; content access separate |
| Create research case | Optional | Yes | Optional | Yes |
| Upload assets | Optional | Yes | Dataset-scoped | Configuration dependent |
| Run approved inference | Yes, if permitted | Yes | Yes, compatible tasks | Operational/testing scope |
| Run training experiments | No by default | Optional | Yes | No by default |
| View EDA | Read | Read | Full within authorization | Registry oversight |
| Review result | Yes | Optional | Technical review | Not automatic |
| Export report | Authorized cases | Authorized cases | Evaluation reports | Authorized scope |
| Assign roles | No | No | No | Yes, audited |
| Register model | No | No | Yes or delegated | Yes or delegated |
| Approve model | No by default | No by default | Separate approval permission | Yes/delegated approver |
| View audit logs | Limited | Limited | Limited | Authorized audit scope |

Implement explicit permissions and resource ownership checks, not only frontend visibility.

## 5. Global Application Shell and Navigation

### 5.1 Layout
- Persistent left sidebar on desktop; collapsible drawer on small screens.
- Top header with product identity, optional workspace selector, case search, notifications, help, profile, and sign out.
- Central page area with title, breadcrumbs, filters/actions, content, and status/error states.
- Responsive layout with keyboard-accessible controls and sufficient contrast.

### 5.2 Primary navigation
- Dashboard
- Cases
- Data & Uploads
- Analysis
- Evaluation
- Datasets & EDA
- Models / Experiments (role-dependent)
- Reviews (permission-dependent)
- Reports
- Notifications
- Settings
- Administration (admin permission only)

Only show modules relevant to the user's permissions, but enforce all access restrictions server-side. Direct URL/API access must not bypass permissions.

### 5.3 Required states on all major pages
- Loading state.
- Empty state with useful next action.
- Validation error.
- Permission denied.
- Not found.
- Network/API failure and safe retry.
- Job queued/running/completed/failed; cancelled only if implemented.
- Quarantined or unsupported asset.
- Stale result/model version.
- Export failure.

## 6. Dashboard Requirements

Dashboards must be data-driven; never hardcode counts or score cards.

### 6.1 Researcher Dashboard
Cards:
- Active cases.
- Jobs running/queued.
- Cases/jobs needing attention.
- Completed analyses in the selected time range.

Sections:
1. Quick actions: Create Case, Upload Image, Open Case, Start Analysis, Review Result, Generate Report.
2. Recent activity: timestamp, case ID, action, task, status.
3. Processing jobs: job ID, task, model version, state, progress only if measured, submitted/updated time, allowed retry/cancel.
4. Recent results: case ID, task, model version, available metrics, review state, open result.
5. Data-quality warnings: invalid file, mask alignment issue, missing metadata, duplicate warning, quarantined geometry, missing label.
6. Notifications and review feedback.

Clicking a summary card opens a list filtered to that category. Define the query and state semantics for each card. A sample result must be marked as a sample result, not a validated overall score.

### 6.2 Clinician Dashboard
Cards:
- Authorized cases awaiting review.
- Recently viewed cases.
- Results pending review.
- Flagged technical-quality issues.

Sections:
- Authorized case list.
- Recent analyses.
- Review queue.
- Image-quality and model-output warnings.
- Recent reports and notifications.

Do not rank cases as clinically urgent based only on an unvalidated score. Avoid showing patient clinical details unless the role and use case explicitly authorize them.

### 6.3 Data Scientist / ML Engineer Dashboard
Cards:
- Registered models.
- Experiments running/completed.
- Evaluation jobs failed.
- Dataset warnings/open data-quality findings.

Sections:
- Recent experiments.
- Training/validation progress when available.
- Dataset version and split manifest status.
- Model registry state (draft, evaluation pending, approved for specified research tasks, deprecated).
- Metric comparisons, class support, and error gallery shortcuts.
- Known duplicates, split overlap, missing labels, and geometry problems.

### 6.4 Administrator Dashboard
Cards:
- Active accounts.
- Queued/failed jobs.
- Registered/approved models.
- Storage/system-health summary.

Sections:
- API/database/object storage/worker health.
- Job failures and retry history.
- User/role/security events.
- Dataset manifest and quarantine warnings.
- Model approvals/deprecations.
- Storage and retention.
- Recent audit activity.

Do not expose API keys, passwords, JWT signing secrets, or protected image content through the admin dashboard.

## 7. Patient / Research Subject and Case Management

### 7.1 Student-project privacy rule
Use public/de-identified datasets and synthetic demonstration records by default. Do not enter real patient-identifiable information into the demo. De-identification is more than removing a name: image metadata (including DICOM headers) and text embedded in images may contain identifiers. Any real-world clinical data use needs proper authorization, governance, and security beyond the basic student prototype.

### 7.2 Research subject fields
Support only where available and permitted:
- Internal pseudonymous subject ID.
- Age or age group.
- Gender/sex field using the source dataset's terminology.
- Medical history (optional, restricted).
- Risk factors (optional, restricted).
- Clinical notes (optional, restricted).
- Source dataset / external source reference.
- De-identification status.
- Created/updated timestamps.

Do not infer missing medical history, risk factors, or demographics from the image. For the student demo, these clinical fields may be disabled or left blank unless there is a legitimate de-identified data requirement.

### 7.3 Case fields
- Unique Case ID.
- Optional associated research subject ID.
- Imaging modality.
- Scan/acquisition date where available and appropriately de-identified.
- Anatomical region.
- Uploaded image/study and asset identifiers.
- Source dataset.
- Intended task.
- Upload and validation status.
- Preprocessing status.
- Analysis status.
- Model name/version used for each analysis.
- Case owner / authorized collaborators.
- Review status.
- Research notes.
- Creation/updated timestamps.

### 7.4 Case list page
Support:
- Search by case ID and permitted metadata.
- Filters for modality, anatomy, task, owner, date, status, and review state.
- Sorting and pagination.
- Create/open/archive actions according to permission.
- Empty, loading, error, and access-denied states.
- Table columns: Case ID, modality, anatomy, task, asset count, latest analysis status, model version, review status, updated time, actions.

### 7.5 Create case
Form fields:
1. Case ID: generated or validated unique research identifier.
2. Modality: only supported choices.
3. Anatomy: selected from supported task registry.
4. Intended task.
5. Dataset/source.
6. Optional de-identified metadata and research notes.
7. Owner/workspace according to permissions.

Validate task compatibility before allowing analysis. Aortic or hepatic CT assets must not be silently routed to a coronary model.

### 7.6 Case details tabs
- Overview: metadata, ownership, modality, anatomy, task, current state, warnings.
- Images & Studies: source files, study/series metadata, dimensions/geometry, validation.
- Assets: original, reference annotation, preprocessed asset, prediction, overlay, report artifacts.
- Preprocessing: steps, parameters, errors, derived assets.
- Analyses: jobs, results, model versions, metrics and errors.
- Compare Results: choose compatible analyses and view outputs side by side.
- Reviews & Notes: comments, decisions, reviewer identity/time.
- History: uploads, status transitions, model versions, reviews, exports, archive events.
- Reports: available reports and secure exports.

Keep assets typed and distinct. A prediction is never automatically a reference annotation.

### 7.7 Compare analyses
Display source asset identity, task, model and preprocessing versions, job time/status, overlays, reference annotation if available, compatible metrics, measurement units, and evaluation protocol. Warn when results are not comparable due to different datasets, tasks, labels, geometry, or metrics. Visual differences alone do not establish better accuracy.

## 8. Medical Image Upload and Preprocessing Engine

### 8.1 Upload workflow
1. Select an authorized case.
2. Select supported file(s).
3. Validate extension and actual file content, file size, readability, metadata, and format.
4. Read image dimensions or volume shape and modality metadata.
5. Check annotation alignment and physical geometry where relevant.
6. Compute checksum and detect known duplicates where available.
7. Save immutable source asset and its metadata.
8. Run task-specific preprocessing.
9. Review validation outcome and enable only compatible next actions.

### 8.2 Supported processing capabilities
As specified in the source project, where appropriate to the selected dataset:
- Medical image upload.
- DICOM/image validation.
- Image format conversion.
- Resolution normalization.
- Intensity normalization.
- Noise reduction.
- Contrast enhancement.
- Resizing.
- ROI extraction.
- Slice selection.
- 2D/3D volume preparation.
- Training-time data augmentation.
- Image registration where required.
- Pixel/voxel spacing preservation.

Not every operation should be applied to every modality. Make preprocessing configurable and versioned, and do not assume a generic sequence is safe for every dataset.

### 8.3 Preprocessing pipeline
`Source image/study → validation → metadata/geometry checks → task-specific normalization/processing → ROI/slice selection where required → image-mask alignment verification → derived asset → compatible model input`

### 8.4 Asset statuses
Uploaded, Validated, Warning, Rejected, Quarantined, Preprocessing, Preprocessing Failed, Ready for Analysis.

Quarantined assets cannot be used for training/evaluation until the issue is corrected or formally excluded with a documented decision.

### 8.5 Asset detail page
Show asset ID, case ID, filename, format, size, checksum, dimensions/volume shape, modality/anatomy, source/reference/derived type, geometry/spacing, validation state, preprocessing version/history, linked jobs, and permitted view/download actions.

## 9. Artery Segmentation Engine

### 9.1 Purpose
Identify artery structures and vessel boundaries from supported images/volumes; produce a mask suitable for visualization and downstream analysis.

### 9.2 Features
- Binary or multi-class/instance segmentation according to dataset labels.
- Pixel/voxel classification.
- Artery mask generation.
- Vessel boundary display.
- Post-processing with traceable settings.
- Original image and predicted mask overlays.
- Export of predictions with model/preprocessing provenance.

### 9.3 Candidate architectures in source specification
The original document lists U-Net, U-Net++, Attention U-Net, ResUNet, DeepLabV3+, nnU-Net, 3D U-Net, TransUNet, and Swin-UNet. These are candidates, not a commitment to train every model. Establish a working baseline first; compare alternatives only after input/label alignment and metrics have been verified.

### 9.4 Pipeline
`Validated input → task-specific preprocessing → compatible segmentation model → probability map/logits → threshold/label decoding → optional validated post-processing → saved mask → visualization/metrics`

### 9.5 Requirements
- Preserve probability output where available, not only binary output.
- Use appropriate interpolation for masks (label-preserving/nearest-neighbour).
- Save threshold and post-processing configuration.
- Keep predicted masks separate from reference masks.
- Store model version, input ID, preprocessing version, output shape, and completion/error status.
- Provide error examples and per-image metrics for evaluation sets with valid reference labels.

## 10. Vessel Structure and Centerline Analysis

### 10.1 Features listed in source project
- Vessel centerline extraction and skeletonization.
- Vessel branching detection.
- Vessel length estimation.
- Vessel diameter estimation.
- Vessel continuity analysis.
- Vessel tortuosity analysis.
- Branch identification.
- Cross-sectional area or local diameter variation where supported.

### 10.2 Output requirements
- Mask area in pixels/voxels.
- Number/size of connected components.
- Centerline/skeleton where implemented.
- Branch points and length where method supports them.
- Width in pixels for 2D images when not calibrated.
- Physical diameter/length/area only when calibration or physical spacing and geometry are defensible.
- Measurement method, units, source geometry, and limitations.

**Boundary:** Vessel segmentation alone does not measure blood flow or vessel capacity. These should not be inferred from a mask alone. Any such future feature requires a separate validated methodology and additional data.

## 11. Stenosis Detection and Localization Engine

### 11.1 Purpose
Identify candidate regions of abnormal arterial narrowing using labels and data suitable for the selected task.

### 11.2 Features
- Candidate region identification.
- Stenosis localization.
- Multiple candidate lesion handling.
- Normal/abnormal classification only when the dataset labels support it.
- Lesion scoring and threshold configuration.
- Display of location and supporting overlay.
- Candidate comparison against annotated lesions for evaluation.

### 11.3 Candidate approaches named in source project
CNN classification, object detection, segmentation-based lesion localization, patch-based classification, 2D/3D methods, and hybrid CNN-transformer methods are listed as possible approaches. The implemented choice must be tied to actual label format and available training examples. A vessel mask alone is not sufficient lesion-level supervision.

### 11.4 Stenosis pipeline
`Compatible input → vessel mask/analysis where relevant → candidate generation/model inference → score and location decoding → threshold and post-processing → saved candidates → visualization/evaluation`

### 11.5 Required diagnostics
For a missed annotated lesion, save:
- Original image and original annotation overlay.
- Transformed image and annotation presented to the model.
- Raw outputs/scores before threshold and NMS.
- Class IDs, boxes/masks, and coordinates.
- Threshold, NMS, and filtering settings.
- Candidate-to-reference matching result under the documented rule.
- Error reason when determinable.

Do not lower the confidence cutoff just to pass a single sample. Tune threshold on validation data, inspect precision/recall or FROC, and document the false-positive trade-off.

## 12. Stenosis Severity Assessment Engine

### 12.1 Severity categories in source specification
Normal, Mild, Moderate, Severe, Critical/Very Severe. Exact thresholds must be drawn from the selected dataset and validated reference standard; the software must not assign arbitrary clinical thresholds.

### 12.2 Possible quantitative estimate
The source specification gives:
`Stenosis Percentage = ((D_reference - D_stenosis) / D_reference) × 100`

Where:
- `D_reference` is an appropriate reference diameter.
- `D_stenosis` is the minimum diameter at the suspected narrowing.

The application must record how these values were measured, whether calibration or voxel spacing is available, and the uncertainty/limitations. Without suitable geometry and reference measurement, show the result as unavailable/experimental rather than a precise physical estimate.

### 12.3 Output fields, when supported
- Candidate location.
- Minimum measured diameter and units.
- Reference diameter and units.
- Estimated percentage narrowing.
- Severity category.
- Score/confidence with clear definition.
- Measurement method and limitations.
- Model/algorithm version and review status.

No severity class should be inferred from mask width alone unless the method is validated for the specific use.

## 13. Explainability and Visualization

### 13.1 Features from source specification
- Segmentation overlays.
- Stenosis localization maps.
- Confidence scores where defined.
- Prediction comparisons.
- Grad-CAM/Grad-CAM++ or attention maps for compatible models.
- Captum or equivalent methods where supported by implementation.

### 13.2 Image analysis screen
Display:
- Original image.
- Preprocessed image.
- Reference mask, where available.
- Predicted artery mask.
- Centerline/skeleton where available.
- Candidate stenosis regions.
- Explanation overlay where implemented.
- Metrics if a valid reference exists.
- Model version, task, threshold, and limitations.

### 13.3 Viewer requirements
- Zoom/pan/reset and fit-to-screen.
- Toggle layers independently.
- Adjust overlay opacity.
- Clear legend differentiating predicted vs reference regions.
- 3D slice navigation and orientation information where a 3D viewer is implemented.
- Export or capture an authorized visualization for reports.
- Keep the same coordinate frame for source, prediction, and reference overlays.

Explainability visuals are supporting illustrations, not proof that a model used medically correct reasoning.

## 14. Training, Evaluation, and Model Lifecycle

### 14.1 Training lifecycle
- Dataset loading and manifest validation.
- Train/validation/test separation.
- Training-only augmentation.
- Training runs and hyperparameter configuration.
- Checkpoint saving.
- Early stopping and learning-rate scheduling where implemented.
- Reproducibility metadata and experiment history.
- Model artifact registration and comparison.

### 14.2 Candidate model/technique names from source specification
Source candidates include ResNet, EfficientNet, DenseNet, U-Net family, DeepLabV3+, nnU-Net, Vision Transformer, Swin Transformer, TransUNet, attention mechanisms, transfer learning, fine-tuning, ensembles, multi-scale features, feature fusion, data augmentation, and class-imbalance handling. These must be evaluated only where suitable data, labels, compute, and a valid baseline are available.

### 14.3 Segmentation metrics
- Dice coefficient.
- IoU.
- Pixel/voxel accuracy where useful.
- Precision.
- Recall/sensitivity.
- Specificity.
- Hausdorff distance and average surface distance when geometry and labels support them.

### 14.4 Detection metrics
- Precision, recall, F1.
- Sensitivity/specificity where the unit and label definition permit.
- AUC-ROC where valid.
- False-positive and false-negative rates.
- Lesion-level sensitivity and false positives per case.
- FROC where appropriate to the detection task.

### 14.5 Severity metrics
- Accuracy and macro/weighted F1 for supported categories.
- Confusion matrix and per-class support.
- AUC only where class/label structure permits.
- MAE/RMSE and agreement/bias measures for continuous severity estimates, when reference measurements exist.

### 14.6 Correct evaluation rules
- Verify metric implementation on known examples.
- Report both per-case distribution and aggregate metrics; label global/micro versus mean-per-image aggregation.
- Report sample count and class support.
- Keep validation separate from final test.
- Tune thresholds/hyperparameters on validation only.
- State the split grouping level and whether patient/study independence is known.
- Never use EDA counts as performance metrics.
- Keep training metrics, validation metrics, final test metrics, and two-sample inference results separate.

### 14.7 Current sample-run observations
Reported result from a run of two fixed test images:
- Artery segmentation: Dice 77.36%, precision 92.30%, recall 66.58% on the reported ARCADE image/result.
- Vessel analysis: mask area, connected components, and approximate pixel width were saved.
- Stenosis detection: annotated lesion missed in the stenosis sample at score cutoff 0.05.
- A note indicates vessel capacity, blood flow, and physical diameter need additional calibrated data.

Interpretation and required action:
- The precision/recall balance suggests investigating false-negative vessel pixels while monitoring added false positives.
- Verify metric code, aggregation, input/mask alignment, preprocessing, output threshold, and checkpoint/task match before changing architecture.
- Save probability maps and perform threshold analysis on validation data.
- Debug the stenosis example using raw scores, coordinates, class mapping, threshold/NMS/filtering, annotation alignment, and label suitability.
- These observations are not dataset-wide metrics; do not present them as proven overall model performance.

### 14.8 Model Registry
Each model version should store:
- Name and version.
- Supported modality/anatomy/task.
- Artifact/checkpoint reference and hash.
- Preprocessing configuration/version.
- Code/environment versions.
- Dataset and split manifest used for evaluation.
- Metrics, class support, limitations, and approval state.
- Created by/date and approval history.
- Deployment status and rollback reference where implemented.

Suggested states: Draft, Evaluation Pending, Approved for Specified Research Task, Deprecated, Rejected. Approval must be task-scoped.

## 15. Dataset Registry and EDA

### 15.1 EDA dataset inventory
The supplied `EDA_REPORT.md` reports these counts. Units differ; totals must not be interpreted as unique people.

| Dataset / task | Unit | Train | Validation | Test | Total |
|---|---|---:|---:|---:|---:|
| ARCADE syntax | 2D image | 1,000 | 200 | 300 | 1,500 |
| ARCADE stenosis | 2D image | 1,000 | 200 | 300 | 1,500 |
| DCA 134 | 2D image | 93 | 20 | 21 | 134 |
| Stenosis archive | 2D frame | 6,625 | 874 | 826 | 8,325 |
| CADICA corrected | 2D frame | 4,033 | 908 | 1,185 | 6,126 |
| AortaSeg aligned subset | 3D volume | 8 | 2 | 2 | 12 |
| HepaticVessel | 3D volume | 218 | 38 | 46 | 302 |
| ImageCAS | 3D volume | 700 | 150 | 150 | 1,000 |
| ImageCAS-X binary union | 3D volume | 560 | 80 | 160 | 800 |

### 15.2 Key EDA findings and product actions
- **ARCADE syntax:** 512×512 images; mean annotations/image 5.21; median foreground fraction 3.208%.
- **ARCADE stenosis:** 512×512 images; mean annotations/image 1.61; zero-annotation cases must not automatically be treated as healthy.
- **DCA 134:** images are 300×300; patient independence is unverified.
- **Stenosis archive:** filename-derived groups are provisional; release train/test shares 63 of 64 inferred groups.
- **CADICA:** corrected split includes incomplete grade support; p100 absent from validation and p99 absent from test. Do not fabricate grade-level estimates.
- **AortaSeg:** only 12 of 60 pairs passed physical alignment; 48 mismatches are quarantined. Labels are pseudo-labels, and the test set has 2 volumes.
- **HepaticVessel:** anatomy is different from coronary arteries; keep as a separate task/pipeline. Zero-byte `hepaticvessel_335` was excluded.
- **ImageCAS/ImageCAS-X:** reuse cases with different split assignments; not independent external tests without an explicit overlap exclusion protocol.
- **CT preparation:** volumes resized to coarse 128³; original-resolution evaluation is needed for small structures.
- **Duplicates:** 123 shared decoded-image hashes between ARCADE syntax and ARCADE stenosis.
- **Intensity:** sampled normalized intensity values are not raw Hounsfield-unit distributions.

### 15.3 EDA dashboard sections
- Dataset inventory and unit.
- Train/validation/test distribution.
- Image dimensions and volume shapes.
- Label/annotation counts and support.
- Foreground pixel/voxel fraction.
- Intensity histograms with correct units and normalization labels.
- Duplicate and near-duplicate audit status.
- Patient/study group overlap where IDs allow.
- Missing labels, corrupt assets, and geometry mismatch findings.
- Preprocessing impact and exclusions.
- Licensing, attribution, version, manifest, and task definition.

Use colour for EDA graphs/results only where requested. All charts need titles, axis labels, units, legends, sample counts, and captions. EDA charts describe data, not trained model quality.

### 15.4 Data governance
- Freeze and version data manifests, split files, task definitions, and duplicate records before training.
- Keep the 48 geometry-mismatched AortaSeg pairs quarantined until corrected and revalidated.
- Prevent duplicate or patient/study groups from crossing splits where IDs permit.
- Do not treat ImageCAS-X as independent of ImageCAS without explicit case exclusion.
- Preserve dataset license and annotation rights.
- Mark independence as verified, unknown, or not applicable.

## 16. Reports, Notifications, and Alerts

### 16.1 Report types
- Case analysis report.
- Segmentation evaluation report.
- Stenosis detection evaluation report.
- Severity assessment report where supported.
- Dataset EDA report.
- Model comparison/experiment report.

### 16.2 Case report contents
- Report ID and date.
- Research case ID and modality.
- Intended task and source asset IDs.
- Preprocessing configuration/version.
- Model and version.
- Segmentation results and visualizations.
- Vessel structure/measurements where supported.
- Stenosis candidate locations and score/threshold where supported.
- Severity output and measurement basis where supported.
- Reference-based evaluation metrics only when valid labels exist.
- Review status/comments, when applicable.
- Provenance and known limitations.
- Research-use / non-diagnostic disclaimer.

### 16.3 Exports
- PDF report.
- JSON and CSV for structured results where appropriate.
- All exports are access-controlled and logged.
- Do not export hidden metadata or unauthorized patient information.

### 16.4 Notifications
Events:
- Upload rejected or quarantined.
- Preprocessing failed.
- Analysis completed or failed.
- Review requested or returned with changes.
- Report generated.
- Model approval/deprecation changed.
- Security-relevant account changes.

Each notification includes timestamp, event type, short message, read/unread status, and authorized destination. Do not leak case details in notifications to users without access.

### 16.5 Alerts
Source-project alert candidates include stenosis detected, severe stenosis detected, multiple stenotic regions, low-confidence prediction, image-quality issue, and processing failure. In this research prototype, these are technical/model alerts, not validated clinical triage signals. Severity thresholds require a defined reference standard.

## 17. End-to-End User Workflows

### 17.1 Researcher: create case to result report
1. Sign in and load permissions.
2. Create/open an authorized research case.
3. Choose modality, anatomy, and task.
4. Upload source image/study and optional reference label.
5. Validate file, metadata, geometry, and duplicates.
6. Run task-specific preprocessing and record derived asset.
7. Select a compatible model/version and configuration.
8. Submit background job and receive job ID.
9. View queued/running/completed/failed status.
10. Open result with source image, prediction, overlays, metrics where valid, version and limitations.
11. Compare with earlier results or submit for review.
12. Generate and export a traceable report.

### 17.2 Clinician: inspect and review analysis
1. Sign in.
2. Open authorized case/review queue.
3. Inspect source images and annotations.
4. Inspect predictions, vessel/stenosis overlays, measurements, and warnings.
5. Check task, model version, threshold, and limitations.
6. Add comments and record permitted research review decision.
7. Notify case owner; preserve review history.
8. Export an authorized report if needed.

### 17.3 Data Scientist: investigate a model result
1. Open the dataset registry and confirm manifest/splits.
2. Inspect data-quality warnings, duplicates, missing labels, and geometry.
3. Select compatible task/model and reproduce baseline.
4. Inspect per-sample false positives/false negatives and raw probabilities.
5. Run validation-only threshold/loss/augmentation experiments in controlled order.
6. Compare models using fixed, documented split protocol.
7. Save config, checkpoint, metrics, sample count, environment, and limitations.
8. Register candidate model and submit for task-scoped approval.

### 17.4 Administrator: handle a failed job
1. Filter Job Management to failed jobs.
2. Inspect safe error summary, job attempts, worker version, asset references, and validation history.
3. Decide whether failure is transient or caused by bad input/configuration.
4. Retry only when supported and safe.
5. Preserve prior failed attempt and create traceable retry.
6. Log important action and notify the authorized owner.

### 17.5 Dataset owner: resolve EDA warning
1. Open dataset version and the finding.
2. Inspect affected sample/asset IDs and evidence.
3. Mark finding Open, Investigating, Resolved, or Accepted with reason.
4. If labels, exclusions, or splits change, create a new manifest/version.
5. Rerun the affected EDA checks and preserve the previous report.

### 17.6 Workflow state diagram
`User request → authorization → input validation → task compatibility → preprocessing → queued job → inference/evaluation → outputs and provenance saved → review/compare → report/export`

At every stage, failures must be persisted with clear status. Refreshing the browser must not erase job state.

## 18. Proposed Technical Architecture and Technology

The source document proposes a layered architecture: presentation clients; API gateway/application layer; AI processing and analysis modules; data-processing/model management/evaluation/report generation; storage; infrastructure monitoring and security; and optional external integrations. The application should preserve this separation even if the implementation uses fewer deployable services initially.

### 18.1 Logical layers
1. **Presentation layer:** React web application, dashboards, forms, image viewer, reports. Mobile interface is optional.
2. **API/application layer:** authentication, RBAC, request validation, case/asset management, task routing, rate limiting, logging.
3. **Analysis layer:** preprocessing, segmentation, vessel analysis, stenosis detection, severity estimation, explainability where implemented.
4. **ML operations layer:** dataset manifests, training runs, model registry, experiment tracking, evaluation.
5. **Storage layer:** relational metadata, original/derived images, masks, models, reports, logs/backups.
6. **Infrastructure layer:** deployment, containerization, secrets, monitoring, backup, availability, resource management.
7. **External integrations (optional):** PACS/HIS/DICOM or external systems only after a justified security and integration review.

### 18.2 Proposed stack from original project document
- Language: Python.
- Backend: FastAPI, REST APIs, Pydantic, SQLAlchemy.
- Frontend: React, JavaScript/TypeScript, Tailwind CSS.
- Charts: Chart.js or Plotly.
- Primary database: PostgreSQL; MongoDB is optional only if justified.
- Medical image storage: local storage for controlled development or object storage such as AWS S3/Azure Blob in deployment.
- ML: PyTorch or TensorFlow; MONAI for medical imaging where appropriate; scikit-learn, NumPy, Pandas, OpenCV.
- Medical image tools: DICOM, pydicom, SimpleITK, NiBabel, OpenCV.
- Segmentation candidates: U-Net, U-Net++, Attention U-Net, DeepLabV3+, nnU-Net, TransUNet, Swin variants.
- Classification/detection candidates: ResNet, EfficientNet, DenseNet, Vision Transformer.
- Explainability: Grad-CAM/Grad-CAM++ or Captum for compatible models.
- MLOps: MLflow, Docker, Docker Compose, GitHub Actions.
- Deployment: AWS/Azure or another explicitly selected cloud environment.
- Tools: VS Code, Git/GitHub, Postman, Jupyter Notebook.

This is a set of candidates from the source document, not a mandate to use every tool. The team should choose one backend, one primary ML framework, one relational database, and a storage strategy. Do not add redundant frameworks without a documented reason.

### 18.3 Suggested API surface
These are proposed routes to adapt to actual code:
- `GET /me`, `GET /me/permissions`
- `POST /cases`, `GET /cases`, `GET /cases/{id}`, `PATCH /cases/{id}`, `POST /cases/{id}/archive`
- `POST /cases/{id}/assets`, `GET /cases/{id}/assets`, `GET /assets/{id}`, `GET /assets/{id}/validation`
- `POST /assets/{id}/preprocessing`
- `POST /cases/{id}/analysis`, `GET /analysis-jobs/{id}`, `POST /analysis-jobs/{id}/retry`, `GET /analysis-results/{id}`
- `GET /reviews`, `GET /reviews/{id}`, `POST /reviews/{id}/decision`, `POST /reviews/{id}/comments`
- `GET /datasets`, `GET /datasets/{id}/manifest`, `GET /datasets/{id}/eda`
- `GET /models`, `GET /models/{id}` and restricted model registration/approval endpoints
- `POST /reports`, `GET /reports/{id}`
- `GET /notifications`, `PATCH /notifications/{id}/read`
- Restricted audit log endpoints.

Use OpenAPI documentation and schema validation. Every endpoint needs authentication/authorization behavior, request and response schemas, failure codes, and tests.

## 19. Data Model

Core entities and relationships:

| Entity | Purpose / required data |
|---|---|
| User | Identity-provider ID, profile, status, timestamps |
| Role / Permission | Role names and explicit actions/scopes |
| UserRole | Role assignments and who granted them |
| Workspace | Owner/group, membership, settings |
| ResearchSubject | Pseudonymous ID, permitted demographic/clinical metadata, de-identification status |
| Case | Case ID, subject reference, owner, modality, anatomy, task, status, timestamps |
| Asset | Case reference, source/derived type, storage key, checksum, dimensions, spacing/orientation, validation status |
| Dataset | Name, source, license, version, task semantics, manifest and split references |
| EDAFinding | Dataset version, finding type, affected IDs, evidence, status/resolution |
| AnalysisJob | Case/asset, task, model version, state, attempts, timestamps, errors |
| AnalysisResult | Job reference, outputs, metrics, measurements, limitations, provenance |
| ModelVersion | Artifact/hash, task compatibility, preprocessing config, environment, metrics, approval state |
| ExperimentRun | Dataset/split version, parameters, seed, curves, checkpoint, metrics |
| Review | Reviewer, linked result version, decision, comments, timestamps |
| Report | Result reference, format, storage key, permissions, creation time |
| Notification | Recipient, event type, read status, timestamp |
| AuditEvent | Actor, action, resource, outcome, timestamp |

Use foreign keys/relationship constraints, indexes, immutable history where needed, and explicit retention rules. Keep personal/subject metadata separated from imaging assets where practical. Never expose raw storage paths or protected metadata through general API responses.

## 20. Non-Functional Requirements

### 20.1 Security and privacy
- TLS for network traffic.
- Secure password hashing; never store plaintext passwords.
- JWT/session expiry and revocation strategy.
- HttpOnly secure cookies where appropriate for the architecture; protect cookie-based flows against CSRF.
- Keep signing secrets and API keys out of source control and frontend bundles.
- Deny access by default and enforce case/asset/report permissions server-side.
- Validate uploads against actual content; guard against oversized/corrupt files and unsafe path handling.
- Audit authentication failures, role/permission changes, exports, model approvals, and sensitive administrative actions.
- Minimize patient-identifying data and use de-identified public datasets for the student demo.

### 20.2 Reliability
- A failed job must never be shown as completed.
- Preserve original assets and historical results.
- Use safe retries and idempotency.
- Record errors with useful context without exposing secrets.
- Keep job status on the backend so browser refresh does not lose it.

### 20.3 Performance and scalability
- Use background jobs for long preprocessing, 3D volumes, training, and reports.
- Avoid loading entire large volumes into browser memory unnecessarily.
- Measure inference, preprocessing, API, dashboard, and report-generation latency on representative data.
- Set numeric limits only after profiling, unless an operational requirement already defines them.

### 20.4 Usability and accessibility
- Consistent navigation, breadcrumbs, titles, status labels, keyboard accessibility, and responsive layouts.
- Every chart has title, axes, units, legend, sample count, and caption.
- Display units (pixels, voxels, mm) correctly.
- Distinguish reference labels, predictions, EDA statistics, validation metrics, and final test metrics.
- Provide clear upload errors, job errors, and safe recovery actions.

### 20.5 Reproducibility
- Track dataset version, split manifest, preprocessing version, code version, model/checkpoint version, configuration, environment, and timestamps.
- Save per-image metrics and output references.
- Preserve evaluation reports and experiment history.
- State grouping level and unknown patient independence.
- Never tune on final test data.

## 21. Acceptance Criteria and Testing

### 21.1 Authentication and roles
- Each role can sign in and sees the appropriate dashboard.
- Invalid/expired sessions and disabled accounts are rejected.
- Direct API calls cannot bypass role or case permissions.
- Session logout/revocation follows the documented design.
- Sensitive actions create audit records.

### 21.2 Case and asset handling
- Case creation validates unique case IDs and required fields.
- User sees only authorized cases.
- Supported image uploads are validated, checksummed, and stored securely.
- Corrupt/unsupported uploads are rejected with useful errors.
- Geometry mismatches are detected and quarantined.
- Original asset and derived asset references remain distinct.

### 21.3 Analysis
- Incompatible modality/anatomy/task/model combinations are rejected.
- Job states are persistent and correct.
- Predictions, reference annotations, and processed inputs are distinguishable.
- Metrics run on known test arrays and have explicit empty-mask policy.
- Metric aggregation, sample count, thresholds, and split are recorded.
- Stenosis detector outputs preserve raw scores and coordinates for debugging.
- Calibrated physical measurements are only shown when the required geometry exists.

### 21.4 EDA, evaluation, reports
- EDA inventory uses correct sample units and does not claim unique patients.
- Known duplicate, overlap, grade support, and geometry warnings are visible.
- EDA is separate from trained-model performance.
- Reports include provenance, metrics where valid, sample counts, model/preprocessing versions, and limitations.
- Authorized exports are logged.
- No claim of clinical validation appears without supporting evidence.

### 21.5 Engineering quality
- Unit tests cover metric calculations, image/mask transforms, role/permission logic, task routing, and output parsing.
- Integration tests cover upload-to-analysis-to-result/report.
- API tests cover successful and denied access paths.
- Linting, type checking, tests, and production build pass.
- Docker image/container workflow is documented and reproducible if deployment phase is in scope.
- Codex reports actual commands and outputs; it must not say a test passed if it was not run.

## 22. Delivery Roadmap and 8-Week Milestones

### Milestone 1 — Weeks 1–2: Project initialization, datasets, core setup
Tasks:
- Finalize intended scope, modality, anatomy, task definitions, and dataset sources/licensing.
- Understand dataset structure and annotations; complete EDA.
- Freeze manifests and review duplicate/split/geometry risks.
- Design architecture, database schema, and UI wireframes.
- Set up frontend/backend, authentication, case management, upload, and baseline preprocessing.

Expected outcome:
- Architecture and data plan documented.
- Dataset manifests and EDA available.
- Frontend/backend initialized.
- Authentication, authorized case flow, upload, and basic preprocessing operational.

### Milestone 2 — Weeks 3–4: Artery segmentation and vessel analysis
Tasks:
- Establish and reproduce baseline segmentation.
- Train/evaluate segmentation model(s).
- Generate artery masks and visualizations.
- Add validated post-processing.
- Extract vessel structures/centerlines where supported.
- Estimate width/diameter only with valid units/calibration.
- Compare models and create a segmentation report.

Expected outcome:
- Segmentation pipeline operational for a clearly defined task.
- Masks/overlays generated and saved.
- Metrics available on valid evaluation splits.
- Vessel analysis produces traceable results.

### Milestone 3 — Weeks 5–6: Stenosis detection, severity, explainability
Tasks:
- Confirm suitable lesion labels.
- Debug localization and coordinate transforms.
- Train/evaluate detection or lesion-segmentation pipeline.
- Implement severity classification/measurement only where reference standards support it.
- Add explainability views and stenosis overlays.
- Build analysis dashboard sections for candidate findings.

Expected outcome:
- Stenosis detection/localization evaluated with appropriate metrics.
- Severity module is either supported with defensible data or explicitly marked experimental/blocked.
- Explainability views are available for compatible models.
- Limitations and false negatives are recorded.

### Milestone 4 — Weeks 7–8: Reporting, testing, analytics, deployment
Tasks:
- Finish dashboards and role-specific workflow.
- Implement PDF/CSV/JSON report export as supported.
- Model comparison and versioning.
- End-to-end, API, security, and performance tests.
- Dockerize application and deploy to selected environment if feasible.
- Configure monitoring/logging.
- Prepare documentation, user guide, final presentation, and demo.

Expected outcome:
- End-to-end research workflow demonstrated.
- Reports generated with traceability.
- Tests and security checks documented.
- Deployment and demo instructions available.

### Priority ordering
P0: auth/RBAC, case/asset handling, validation, job persistence, traceability.  
P1: one reliable segmentation flow, visualization, valid evaluation, report generation.  
P2: review workflow, EDA dashboard, model registry, stenosis localization.  
P3: severity measurements, advanced explainability, 3D viewer, integrations, cloud scaling—only after dependencies and validation requirements are met.

## 23. Risks, Dependencies, and Open Decisions

### 23.1 Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Role/security gaps | Unauthorized case or asset access | Server-side RBAC, resource checks, integration tests, audit logs |
| Real identifiable patient data in student demo | Privacy exposure | Use public/de-identified data and synthetic records |
| Wrong image/mask geometry | Invalid supervision and metrics | Geometry validation, transform tests, quarantine mismatches |
| Duplicate/split overlap | Inflated estimates of generalization | Manifest/duplicate audits and leakage-aware grouped splits |
| Missing labels/grade support | Misleading estimates | Show class support; do not fabricate scores |
| Pseudo-labels treated as ground truth | Misleading evaluation | Track provenance and label type |
| Low segmentation recall | Missed vessel pixels | Error review, threshold validation, sampling/loss/resolution experiments |
| Missed stenosis lesion | False reassurance if misinterpreted | Debug raw scores/coordinates/labels; use proper lesion-level validation |
| Pixel widths mistaken for mm | Invalid measurements | Clear units and require calibration/spacing |
| Severe performance claims from two samples | Invalid generalization claim | Label sample inference separately; run held-out evaluation |
| Coarse 128³ volume preparation | Small structures lost | Original-resolution evaluation and spacing preservation |
| Scope creep / too many architectures | Delayed reliable release | Establish one baseline; staged experiments |

### 23.2 Open decisions for the team
- First-release primary modality/anatomy/task: choose a concrete benchmark.
- Exact dataset(s) to use for the first public demo and license constraints.
- Whether clinician-facing clinical metadata fields remain hidden/disabled for the student prototype.
- Authentication method: library/framework, JWT/session storage, refresh/revocation strategy.
- Supported upload formats and limits.
- Primary ML framework (PyTorch or TensorFlow) and whether MONAI is needed.
- Database and object-storage provider.
- How reviewer permissions are assigned.
- Who can register/approve model versions.
- Whether severity is categorical or numerical and which reference standard supports it.
- Numeric latency/throughput targets after profiling.
- Deployment target and available GPU resources.
- Whether external PACS/HIS/DICOM integration is out of scope for the current demo.

## 24. Codex Implementation Instructions

1. Inspect the repository before changing code. Identify current frontend/backend stack, routing, schema, auth, upload/preprocessing, saved models, evaluation code, and tests.
2. Map every requirement in this PRD to implemented, partial, missing, or blocked.
3. Create a gap report and a file-by-file plan.
4. Establish/reproduce baseline inference and verify metric calculations and image/mask alignment before score optimization.
5. Implement in small phases, starting with P0 foundations and one end-to-end analysis workflow.
6. Add tests for permissions, uploads, geometry, metrics, thresholds, coordinates, jobs, reports, and split checks.
7. Preserve working code and API compatibility unless a justified change is necessary.
8. Do not invent output data, metrics, user counts, successful tests, or training results.
9. Run existing lint/typecheck/test/build commands and quote actual outcomes.
10. Update README, API documentation, configuration examples, and user guide.
11. At each phase report: what was inspected, changed files, decisions, commands/tests run, actual results, remaining issues, and next steps.

## 25. Sources and Disclaimer

This PRD is based on the uploaded *Artery Segmentation and Stenosis Detection Using Advanced DL Techniques* specification (28 pages), the project requirements discussed in recent conversations, and the supplied dataset EDA summary. The uploaded specification provides the project objective, module inventory, candidate technologies/architectures, and 8-week milestones. User-role dashboards, detailed permissions, case workflows, and implementation acceptance criteria are expanded product requirements. Current sample-run metrics are recorded as reported observations and need verification from code/logs before being called general model performance.

**Research-use disclaimer:** CoroVision AI is a research/educational prototype. Its outputs must not be used as a standalone clinical diagnosis or represented as clinically validated without separate evidence and appropriate governance.
