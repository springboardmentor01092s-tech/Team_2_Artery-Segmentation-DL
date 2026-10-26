# Task-specific research inference connections

26 October 2026. Ten enabled task routes/views, two hepatic exclusions. This is
application integration, not ten independently trained or clinically approved models.
CADICA localization and source-grade views use the same original detector.

## Access

- Model Evaluation → Model evaluation → Task connection registry reports current
  hash-verified installation, rather than the historical two-model catalogue.
- Coronary XCA case → Assets & preparation → Choose a task model exposes DCA,
  ARCADE anatomical instances, CADICA localization/source-grade boxes and archive
  lesion boxes. Runs use saved, unenhanced 512-square Standard assets. Original
  artery/stenosis inference remains in its existing analysis workflow.
- Coronary CTA case → volume workflow selects original ImageCAS or ImageCAS-X.
- Aorta CT/CTA case → volume workflow selects AortaSeg. Hepatic and MRA inputs
  cannot reach these adapters. Aorta references were AI pseudo-labels.

The selected task and source image/volume are explicit. Results retain immutable
run IDs, case/image identity, input/checkpoint hashes, thresholds, preprocessing,
runtime and artifacts. New 2D runs use their own persisted table and never replace
the original binary analysis or human assessment. Volume records retain a model
key; legacy rows default to ImageCAS. Restarted queued/running jobs fail explicitly.
Artifact retrieval requires case access; read-only assignments cannot submit work.

## Checkpoints and limits

`backend/app/task_models.py` pins every checkpoint and reconstructs only the
preserved compatible architecture/class map. All new loads use weights_only=True
and strict state-dict loading, with no pretrained network download.
`python scripts/install_task_artifacts.py` copies only verified source checkpoints
into the Git-ignored task release directory and refuses mismatched replacements.
Source packages and the original active release remain unchanged.

DCA uses the separately preserved ResNet34 candidate (hash 654c99dd…, source
package threshold 0.3), not the older CPU256 checkpoint or downloaded unselected
GPU512 file. The UI identifies it as a research candidate; its connection is not
new evidence of superiority. CADICA retains its seven source class IDs and small
anchors; these class strings are not validated clinical severity grades.

ImageCAS-X uses original epoch97 hash 8a978778…, not the quarantined epoch147
resume weights. ImageCAS remains original epoch75. Both downloaded resume
checkpoints remain validation-pending and are not selectable here. All 3D adapters
use their original coarse128, canonical RAS XYZ, [-200,800] HU and float16-storage
roundtrip preprocessing; they do not recover native-resolution detail.

ICA and automatic severity have no eligible verified inference checkpoint or
reference protocol and are not falsely added as functioning models. Hepatic vessel
and tumour tasks remain excluded under the user's prior explicit instruction.

## Verification

Command: CV_VERIFY_TASK_MODELS=1 CV_TASK_IMAGE='../data/processed/arcade/syntax/val/images/1.png' PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_task_inference.py backend/tests/test_volume_inference.py backend/tests/test_evaluation_catalog.py backend/tests/test_research_progress.py -q

Result: 21 passed, 1 skipped in 29.46 seconds. The skipped test is the separate
original ImageCAS opt-in test; its existing integration receipt is preserved.
The enabled real-checkpoint tests execute all five additional 2D task views and
both original ImageCAS-X/Aorta models. The 2D input is a known de-identified ARCADE
frame used solely for execution/geometry checks, not a DCA or CADICA benchmark.
The two 3D checks use a clearly synthetic nonmedical volume and verify restored
source shape/affine. These checks do not validate medical accuracy or native
performance. API tests separately verify authorization, case/image identity,
artifact access, model selection/anatomy isolation and persistence.

Frontend: 14 tests passed; TypeScript and Vite production build passed. The
existing >500kB bundle-size warning remains. Initial unit tests expected 403 for
unrelated cases; the actual privacy-preserving response is 404, and expectations
were corrected without weakening access checks.

No training, optimizer updates, dataset pooling, protected-test tuning, model
promotion, deployment or Git push occurred. A diagnostic accidentally opened an
empty application-root SQLite file; that zero-byte diagnostic file was removed.
The real backend-configured database and user data were preserved.
