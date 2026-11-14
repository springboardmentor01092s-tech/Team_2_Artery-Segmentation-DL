# Requirements traceability — 14 November 2026

Sources include AGENTS.md, the preserved comprehensive PRD, milestone documents and the owner's 2D/3D/master audit requests. The previously supplied PDF exists and contains 21 pages according to `pdfinfo`; it is the Weeks 1–4 report. The referenced original 28-page specification has not been established as that file.

Base revision is `b6a7ac097f583f6e4d298293aa6b3484662880ce`. Local edits are uncommitted and preserved.

| ID | Milestone/module | Implementation / entry point | Coverage / actual evidence | Software status | Scientific status / next action |
| --- | --- | --- | --- | --- | --- |
| M1-A | Authentication/access | `auth_ext.py`, `security.py`, `App.tsx`, `/api/auth/*` | Full regression and installed-checkpoint access test | SOFTWARE_VERIFIED | Browser role walkthrough pending |
| M1-B | Case intake | `main.py`, `CaseWorkflow.tsx`, `/api/cases` | Fresh-case receipts and isolated case tests | SOFTWARE_VERIFIED | Recheck browser upload and restore |
| M1-C | 2D preprocessing | `preprocessing.py`, `VolumeIntake.tsx`, image upload endpoint | Coordinate, format and real-checkpoint smoke tests | SOFTWARE_VERIFIED | Calibration/reference accuracy requires independent evidence |
| M1-D | 3D preprocessing | `volume_preprocessing.py`, `volume_inference.py`, volume intake | Physical geometry fixtures and public CTA receipt | SOFTWARE_VERIFIED | Direct DICOM-to-inference browser flow incomplete |
| M2-A | 2D segmentation | `trained_release.py`, `AnalysisWorkbench.tsx` | Actual frozen checkpoint smoke plus ARCADE release report | DEVELOPMENT_EVALUATED | Independent patient evaluation unavailable |
| M2-B | 2D vessel structure | `analysis_model.py`, `local_diameters.py`, width-profile viewer | Centerline/profile and geometry fixture tests | SOFTWARE_VERIFIED | Retain difficult phantom errors; real anatomical association incomplete |
| M2-C | 3D segmentation | `volume_inference.py`, `VolumeInference.tsx` | Public CTA mask and original-grid geometry receipts | DEVELOPMENT_EVALUATED | Coarse segmentation limits native lumen resolution |
| M2-D | 3D geometry | `volume_measurements.py` | 25 saved paths; physical-cylinder section fixtures | PARTIALLY_IMPLEMENTED | Uncertainty, robust local references, interactive source MPR/CPR pending |
| M3-A | 2D stenosis localization | Preserved detector, candidate viewer | Saved boxes/scores and historical development evidence | DEVELOPMENT_EVALUATED | Independent cohort and detector error audit pending |
| M3-B | 2D measurement/severity | `saved_measurement.py`, `narrowing.py`, `StenosisMeasurements.tsx` | Strict quality tests and explicit exploratory records | SOFTWARE_VERIFIED | Exploratory fallback excludes reference validation and has unquantified uncertainty |
| M3-C | 3D narrowing | `volume_measurements.py`, `volume_reporting.py` | One current perpendicular-section candidate; v2 geometry cache | PARTIALLY_IMPLEMENTED | Reference suitability and uncertainty remain exploratory |
| M3-D | Attribution | Existing XAI metadata/adapter hooks | Integrity tests, no executed current detector attribution artifact | PARTIALLY_IMPLEMENTED | Implement fixed model target and controlled faithfulness measurements |
| M3-E | Manual references | `reference-measurement.html`, `reference_collection.py` | Backend roundtrip tests and historical browser receipt | SOFTWARE_VERIFIED | No independent calibrated real-image measurement pairs |
| M4-A | Reporting | `research_reporting.py`, `volume_reporting.py`, report endpoints | Live 2D and 3D JSON/CSV/PDF/ZIP checks and ZIP member hashes | SOFTWARE_VERIFIED | Browser downloads pending |
| M4-B | Models/research | `ModelWorkspace.tsx`, `task_models.py` | Hash-pinned registry and recorded metric tables | SOFTWARE_VERIFIED | Additional task models not all re-executed in this session |
| M4-C | Operations | health, jobs, audit, backup | Regression fixtures and preserved backup receipts | PARTIALLY_IMPLEMENTED | Docker unavailable; sustained inference capacity unmeasured |

No row currently qualifies as independently evaluated based on this session. Each screen requires real browser verification before BROWSER_VERIFIED status can be assigned.
