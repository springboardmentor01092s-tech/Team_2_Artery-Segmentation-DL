# Segmentation deliverables — actual execution evidence, 29 October 2026

## Stenosis improvement preparation

Saved v1 IoU50 diagnosis verified: TP195 FP369 FN211 on 200 validation frames;
instance F1 .402062, matched-instance Dice .801904. Missed lesions and false
positives require evaluation separately from union Dice. A disabled single
operating-point trial (.25 -> .15 detection threshold, unchanged weights and
pixel threshold) is predeclared outside the app. Acceptance requires >=.02
instance-F1 gain, no recall/union-Dice/task-F1 loss, precision drop <=.02 and
FP/frame increase <=.10. No new run, tuning sweep or improvement claimed.
Actual immutable inputs/cohort hashes and baseline parity remain unverified;
this chat has no Chrome-control tool and HP SSD is unmounted. Production unchanged.
See research experiments/advanced_preparation_20261026/STENOSIS_IMPROVEMENT_20261029.md.

## Public stenosis reference search

Verified source candidates: CADICA V5 publishes CC BY 4.0 expert severity boxes;
official DiGDA relabel publishes CC BY-NC-SA 4.0 two-class ARCADE severity boxes;
CCA-200 public 20-case CTA training subset declares GPL-3.0 and 0.5mm expert
lumen annotations. ASOCA currently requires depositor permission under UKDS EUL.
No single inspected open release establishes calibrated 2D images plus reviewed
lesion-local/reference mm diameters and severity truth. These candidates do not
clear clinical grading. Source-specific metadata contracts and synthetic tests
were added outside the app. Full evidence: research
experiments/advanced_preparation_20261026/PUBLIC_STENOSIS_REFERENCES_20261029.md.

## Stenosis implementation follow-up

New reviewed measurement history, clinician-only entry, narrowing arithmetic,
configurable referenced research severity engine and JSON/CSV/PDF snapshot
integration implemented. Live model job c8b43fbd-1c1f-49d4-a2a1-2189c9ba9ff9
completed; event 9568e91f-8f0d-4661-8f2c-41d2b30f0031 produced one candidate,
833 mask pixels and saved bounds/polygon/overlays/explanation. No real reviewed
diameter or severity reference protocol exists; severity remains unavailable.
No new training, Grad-CAM validation or clinical accuracy claim. Full details:
`reports/research_progress/STENOSIS_DELIVERY_20261029.md`.

## DCA source intake follow-up

Separate traceable Mendeley DOI 10.17632/4wvf54td8d.1 V1 download verified:
all 268 local PGM files are byte-identical to archive members, archive SHA256
matches provider 0b05f8fa765e89262988bf33a53229b4c2faaafe7d00e4f310bc725642f6a28d.
Published license CC BY 4.0 retained with attribution. Existing files unchanged.
This clears the missing release/local hash link, not every execution gate.
Archive split 93/13/28 differs from checkpoint 93/20/21; trace exposure before
an unseen/protected-test claim. No model execution or new metrics. Detailed
receipt: research experiments/advanced_preparation_20261026/DCA_TRACEABLE_INTAKE_20261029.md.
Exact split join shows 19 archive-Test IDs in checkpoint training and three in
checkpoint validation. These checkpoints cannot support a preserved archive-test
holdout claim. Both original split records remain unchanged.

This is an acceptance record, not a claim that every requested task is complete.
Baseline application inference was explicitly requested and executed locally.
Research training/evaluation remains Kaggle-only. No optimizer or training ran.

| Requested task | Status and proof |
| --- | --- |
| Baseline segmentation model | IMPLEMENTED / RUN VERIFIED. Preserved trained 2D adapter `backend/app/trained_release.py`, architecture `preserved_models.py`; model version corovision-preserved-2d-20261023 |
| Advanced segmentation architecture | IMPLEMENTED / UNTRAINED. Separate research `advanced_models.py` includes Attention U-Net, U-Net++ and configurable 3D U-Net; not official nnU-Net integration. Full research suite 110 passed in 1.68s |
| Train segmentation models | HISTORICAL BASELINES EXIST / ADVANCED TRAINING PENDING. User's latest request explicitly includes training; this supersedes the previous freeze for this requested work, subject to original Kaggle/resource/data/budget gates. No new training run or advanced checkpoint exists |
| Generate artery masks | RUN VERIFIED. Fresh saved event 7974f2f0-2d49-453a-b8b7-1e0febebf51d, image 7b62cf5c-7deb-4a38-bfa7-e8bcfafa5ac6; artery mask 8,927 pixels |
| Segmentation post-processing | IMPLEMENTED / SOFTWARE VERIFIED. analysis_model.postprocess_mask removes tiny components for geometry. The separate fixed-hole research candidate was rejected; do not describe it as an accepted improvement |
| Extract vessel structures | RUN VERIFIED / ANATOMICAL VALIDATION PENDING. Fresh output includes graph paths, 2 junctions and 4 endpoints |
| Centerline extraction | RUN VERIFIED / ANATOMICAL VALIDATION PENDING. Saved centerline panel and graph; length 797.96 px |
| Vessel diameter | ESTIMATE IMPLEMENTED / REFERENCE VALIDATION PENDING. Approximate mean mask width 12.08 px; calibration unavailable, not a validated physical lumen diameter |
| Compare segmentation models | HISTORICAL RESULTS / ADVANCED COMPARISON PENDING. Existing baseline development-validation values and rejected frozen postprocessing comparison are available. Neither is a trained Attention-versus-baseline comparison |
| Segmentation performance reports | EXISTING REPORTS / ADVANCED REPORT PENDING. Saved run has historical baseline validation Dice 0.8272773138933874 and IoU 0.7122207162851368 on 200 development-exposed cases. No ground truth was supplied for this demonstration image; image-specific accuracy unavailable |

## Running-code receipt

Command from application root: `backend/.venv/bin/python scripts/demo_code_to_outputs.py`.
Job 7c455aec-c2b3-4902-b76c-2677a8643836 progressed pending -> processing -> completed.
Result event and image IDs above were asserted against API responses.
Saved result JSON and six actual downloaded PNG panels: original, processed,
artery_mask, centerline, boundary and overlay, under
`reports/live_code_demo_404fa048/`. No synthetic prediction was inserted.
These are also available through the image's saved analysis in the application.

Application tests: `tests/test_vessel_centerline.py tests/test_standard_pipelines.py
tests/test_review_reporting.py tests/test_research_progress.py`: 30 passed in
7.03s; one Starlette/httpx deprecation warning. Tests cover synthetic geometry,
pipeline/report identity and evidence authorization; they are not clinical tests.

Research tests: `PYTHONPATH=. .git-publish/backend/.venv/bin/python -m pytest
research_optimization/tests -q`: 110 passed in 1.68s. Synthetic/metadata checks
do not establish trained accuracy or real anatomical correctness.

## Remaining gates

Live application verification after a safe restart (zero queued/running 2D and
3D jobs): authenticated Research Progress returned seven focused proof entries;
the new evidence endpoint returned HTTP 200 and the saved event ID matched.
Receipt: `segmentation_api_verification_20261029.json`. Application Git whitespace
check passed. Initial direct database checks omitted backend/.env and failed on
an uninitialized default database; rechecking with the actual application
configuration succeeded. No application records were reset or migrated.

Authorized workspace: mokshagnamannam. Browser-control tools are unavailable in
this session, so remote free resources/input versions cannot be verified or a
job dispatched. Do not substitute local research execution or another account.
Advanced input/label/normalization contract, exact source/reference mapping,
rights/exposure and finite predeclared training protocol remain to be cleared.
ARCADE 996 saved hash mismatches follow a fully traced lexicographic permutation;
annotation correspondence and remote-release identity are still unverified.
Preserve all original models, splits and historical evidence; no auto-promotion.

## 29 October continuation evidence

The authorized Kaggle account was reverified in Chrome as Mokshagna Mannam with
30/30 GPU hours and zero active events. No session was started. The proposed
independent-training notebook has no completed saved version, so it is not an
executable pinned trial. Historical DCA notebook version 2/run 358570780 and its
93/20/21 input manifest were visible, but an immutable attached-dataset version
was not exposed.

A fresh metadata-only ARCADE audit verified 1,000/1,000 syntax/stenosis
validation/test rows against preserved COCO image IDs and filenames; processed
stenosis label JSON also exactly matched the corresponding local COCO annotations.
This does not prove raster alignment or local-to-Kaggle release equivalence.
A disabled DCA 20-case frozen-ensemble protocol now pins member and cohort hashes,
geometry, equal-probability fusion, threshold, metrics and regression gates.
Missing remote byte identity, dataset-version, rights/exposure, all-case geometry
and probability-cache evidence blocked execution. No training, inference,
candidate metric, checkpoint or improvement was produced.

Further DCA gate work verified all 20 validation image/reference hashes and
300x300 geometry, mutually disjoint 93/20/21 split IDs and image hashes, the
inverse probability-grid contract, semantic equality of the downloaded Kaggle
manifest, and byte identity of the downloaded/local GPU checkpoint. The CPU
checkpoint still has no immutable Kaggle file/version binding. A later traceable
Mendeley intake established all 268 local PGM bytes match the CC BY 4.0 release,
but also proved the provider 93/13/28 split differs from the checkpoint 93/20/21
split: 19 provider-test IDs occur in checkpoint training and three in validation.
The protocol therefore remains disabled and cannot claim a provider holdout. See
`experiments/advanced_preparation_20261026/DCA_EXECUTION_GATE_STATUS_20261029.md`
and `DCA_TRACEABLE_INTAKE_20261029.md`. No new trial or improvement claim.

## Stenosis/XAI continuation

Method-specific Grad-CAM software now preserves the exact model-input frame and
saves target, layer, mapping and no-weight-update provenance; unsupported
adapters fail closed. Synthetic integrity tests passed, and the frontend
production build passed. This is not a Kaggle attribution run or faithfulness
validation. Stenosis training was not launched because Chrome-based account,
resource, active-job and immutable remote-version checks are unavailable and the
local ARCADE source contract still has unresolved mapping/version fields. See
`STENOSIS_XAI_CONTINUATION_20261029.md`.
