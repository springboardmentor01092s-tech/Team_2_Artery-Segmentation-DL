# Project requirements acceptance matrix — 20 November 2026

| Requirement | Code | Actual test | Browser | Provenance | Research status | Remaining blocker | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2D artery segmentation | Implemented | Full regression | Historical | Checkpoint hash locked | Development evaluated | Independent cohort | PARTIAL |
| Stenosis candidates/localization | Implemented | Full + focused XAI tests | Historical | Mask R-CNN hash locked | Development evaluated | Independent localization reference | PARTIAL |
| 2D MLD/RVD and narrowing | Experimental | Synthetic and saved-run tests | Historical | Run-bound | Research only | Calibrated QCA/qualified references | PARTIAL |
| Research severity | Implemented with abstention | Protocol/export tests | Historical | Snapshot bound | Experimental | Independent severity agreement | PARTIAL |
| 3D segmentation/viewer | Implemented | Volume regression | Fresh NIfTI and direct-series journeys | Saved model output | Engineering verified | Independent real coronary CTA evaluation | PARTIAL |
| 3D measurement/severity | Bilateral local v5 | Synthetic anisotropic narrowing/taper/sensitivity | Historical | Source-grid bound | Experimental | Statistical uncertainty and CTA reference | PARTIAL |
| DICOM/NIfTI intake | Implemented | Automated input tests | Fresh XA DICOM, direct-series and NIfTI journeys | Parser/geometry receipts + exact run IDs | Engineering verified | Real-series scientific/production acceptance | PARTIAL |
| Explainability | Candidate Grad-CAM/activation | Candidate-bound: 1/3 complete perturbation pass | Candidate-aligned UI previously observed | Checkpoint bound | Faithfulness not established | Consistent perturbation + randomization acceptance | PARTIAL |
| Saved runs/reports | Implemented | Authorization, consistency and DICOM-printable-source regression | Fresh PNG/JPEG/XA DICOM/volume save-reopen passed; PNG JSON/CSV/PDF/ZIP reconciled; XA DICOM v2 PDF visually verified with original + overlay | Immutable versioned snapshot | Engineering verified for tested inputs | Broader production/operations acceptance | PARTIAL |
| Roles/security | Implemented only in uncommitted local workspace | 333 backend + 20 frontend, MFA/invitation and anonymous-route checks | Seven demo roles plus local Docker first-admin, MFA and invitation browser workflow passed | Local-release evidence | Software verified locally | Clean GitHub revision lacks the invitation endpoint; publish reviewed source then repeat acceptance | BLOCKED |
| Full automated regression | Implemented | 333 backend + 20 frontend; prior production build passed | Local Docker Chromium acceptance | Working-tree evidence recorded | Software verified | Five opt-in external/model checks skipped | PASS |
| Deployment | Prepared locally | Not deployed | NOT_TESTED | N/A | Postponed | Authorization and production architecture | BLOCKED |
| Independent clinical validation | N/A | No eligible evidence | N/A | Missing reference cohort | Not established | External clinical evidence/governance | BLOCKED |

## Final decision

The application is a defensible research software demonstration with strong automated and fresh browser evidence. The intended input-format browser matrix and PNG export reconciliation pass. The disposable legacy PostgreSQL check passed. Full project acceptance remains **PARTIAL** because independent evaluation, explainability faithfulness, security acceptance, and hosted verification remain open.

The attempted Kaggle validation version 2 is not scientific evidence: its immutable version history says **Ran in 0 seconds**, and the saved notebook has no execution count or outputs. No optimizer training, threshold result, test-set evaluation or model promotion is claimed from that no-op.

## Closeout decisions by scope

| Area | Verified outcome | Remaining acceptance |
| --- | --- | --- |
| Milestone 1 foundation | PASS for disposable legacy upgrade, PostgreSQL report API, and backup/restore snapshot reconciliation | Hosted recovery remains a separate check |
| Milestone 2 engineering | PASS for tested saved 2D and 3D workflows | Independent segmentation is BLOCKED on verified cohort eligibility and paired native-grid references |
| Milestone 3 engineering | PASS for known-truth geometry and quality-gated output in tested scope | Independent localization, measurement and severity agreement are BLOCKED on calibrated expert references |
| XAI faithfulness | PARTIAL. Candidate-specific attribution is implemented and tested | Mixed perturbation results and unavailable matched randomization target |
| Milestone 4 dashboard, reports and handoff | PASS in the local browser and scoped container checks | Historical comparison lacks independently reproduced case matching |
| Model and threshold selection | BLOCKED. Retained models and research settings are recorded | Eligible validation sweep and frozen decision record |
| Training readiness | BLOCKED. Training is paused | Shared ownership, immutable inputs and live compute quota |
| Container readiness | PARTIAL. Baseline two-job capped queue, exact-run exports, local MFA/invitation workflow, passive access-control checks and bounded liveness probe passed | Debian 13 candidate scan shows 0 critical and 123 high package findings. Cold login Lighthouse LCP was 11.4 s. Security and performance risk disposition remains open |
| Actual deployment and hosted verification | BLOCKED | Selected authorized target |
| Full project acceptance | PARTIAL | Scientific, security and hosted acceptance gates remain open |
