# Integration audit — 25 October 2026

## Verified application

React 19/TypeScript/Vite frontend with role-scoped sidebar state; FastAPI,
SQLAlchemy, existing case/action grants and authenticated artifact routes.
Application checkout is .git-publish; local database and uploads remain private.
Existing inference uses a persistent AnalysisJob worker, immutable AnalysisEvent,
versioned structured result, saved masks/raw scores/overlays and deterministic
evidence explanations. Model activation is not formal research approval.

## Connected drive

The 240gb volume contains CoroVision_Full_20261024, CoroVision_handoff, portable
and offline Kaggle backups. The full transfer reuses files in the handoff directory.
Source paths must be resolved through manifest.jsonl, not guessed or bulk copied.
scripts/audit_connected_handoff.py independently matched 15 evidence files to the
transfer and dataset-audit hashes, found all 12 indexed checkpoint files and
recorded nine task packages. See ../DATASET_COMPATIBILITY_REPORT.md.

| Component | Actual source / application path | Input / output | Status and action |
| --- | --- | --- | --- |
| Artery | drive trained_models/syntax_binary_resnet34_v1; app backend/app/preserved_models.py | grayscale 512, internally RGB/ImageNet; binary mask/raw scores | Same release hash expected; preserve weights and verify bytes |
| Stenosis | drive trained_models/stenosis/models/candidate_01_maskrcnn_resnet50_fpn; app backend/app/trained_release.py | RGB 0–1; instance masks/raw scores, union overlay | Preserve class-26 display mapping; candidates are not confirmed disease |
| Vessel | backend/app/analysis_model.py | artery mask + spacing → graph/diameter/length | Algorithmic research geometry, not a trained model |
| Severity | backend/app/analysis_result.py | validated local/reference measurements required | insufficient_evidence; no approved reference-selection protocol |
| Jobs/results | backend/app/main.py, inference_jobs.py, analysis_result.py | authorized asset → job → stored event/artifacts | Real existing pipeline; regression and real-weight tests required |
| 3D | drive trained_models/imagecas128, imagecasx128, aorta128, hepatic128 | dataset-specific CT volumes / voxel masks | Files present; not application-approved or connected to clinical inference |
| Evaluation | evaluation_workspace.py; frontend ExperimentLab.tsx | immutable imported logs/metrics/artifacts | Connect verified external records without relabelling them approved |

## Risks found

- Generic preview uses thumbnail/Lanczos, while the artery loader uses
  PIL ImageOps.pad/BILINEAR. Non-512 and enhanced inputs cannot be called exact
  training inputs without an explicit recorded model contract.
- Package descriptions and supplied config differ in interpolation wording;
  executable loader and architecture definitions take precedence after inspection.
- Stenosis independent image detector must not be claimed to consume centerlines;
  no vessel-conditioned detector checkpoint has been verified.
- No clinical severity calibration, validated local reference-selection protocol,
  or independent approval record was found. Never fabricate them.
- User-supplied Kaggle old/new accounts are not needed to inspect local backup.
  No password, API credential, remote job or training action has been requested.

No source training script is executed or copied into the inference application.
Raw dataset contents and current remote Kaggle state remain separately unverified.
