# Active execution handoff

Updated 14 October 2026, approximately 12:50–12:55 IST. Historical documents saying
the Mac has no GPU are superseded: **Apple MPS works outside the sandbox**.

## Actual completed result

ARCADE syntax: 12 epochs recorded, validation-selected Mask R-CNN checkpoint.
Final evaluation on 300 official test images completed on Apple MPS.

- Union-mask Dice 0.732144; IoU 0.577466.
- Instance F1 at IoU .50: 0.371389.
- Local ARCADE-style anatomical task F1: 0.133090; this is not independently
  certified against the challenge evaluator and is not a high final task score.
- Output: `output/colab_runs/20261014_syntax/models/individual/syntax/`.
- Weights SHA-256: `2003d12305c0cd58b9abde477e2ed311300fe69f94662b5f470fab20a434031a`.
- No automatic application deployment or registry promotion.

## Running and queued work

1. Colab free T4: stenosis training executing in the existing syntax notebook
   (the additional cell is explicitly scoped to stenosis, separate weights and
   outputs). A stenosis-only final test cell and final ZIP export are queued.
   Link: https://colab.research.google.com/drive/1Y7Wef_uZrYLuwYTW5bqjIngCBUJcXzA7
   Last checked about 34 minutes into that cell. Old duplicate pending CADICA
   cloud cell was removed through its cell menu; verify actual queue behavior.
2. Local CADICA MPS: observed PID **29071**, exec session **99849**.
   `scripts/train_cadica_detector.py --device mps --input-size 512 --batch-size 2
   --workers 0 --epochs 40 --patience 8 --output models/individual/cadica_mps_20261014`.
   Model download completed with normal TLS verification using installed certifi
   CA roots. Training entered `device=mps; input_size=512; start_epoch=0`.
   First completed epoch artifact was not yet observed at this update.
   No claim of completed CADICA training or a final score.
3. Local MSD preprocessing: observed PID **29543**, exec session **16045**.
   Source adapter copied original training NIfTI bytes into `data/nnunet_raw/`;
   original archive, headers and masks remain unchanged. Framework integrity
   passed, fingerprint/planning finished, full-resolution preprocessing began.
   About 17 case property files were observed at an early check, not all 303.
   Default 3D plan: spacing [1.5, 0.798828, 0.798828], patch [64,192,192], batch 2,
   CT normalization. Derived resampling is tracked by nnU-Net for geometry recovery.
4. Local sequential runner: `scripts/continue_local_gpu_queue.py`, exec session
   **43303**, waits for the two observed own PIDs, then runs frozen CADICA final
   evaluation and all five MSD 3D folds with the framework's default full schedule.
   It saves MSD checkpoints every epoch rather than every 50 epochs. This may
   take days on a personal GPU; it is not a short smoke test. Actual status and
   any failures: `reports/local_gpu_queue_state.json`.

Do not run duplicate local trainers. Verify narrowly scoped own PIDs are still
the same tasks before acting; PIDs can become stale. Memory-intensive 3D GPU
training is sequenced after CADICA, not launched concurrently on the same GPU.

## Test evaluation repairs verified

- Single-task final evaluation now honors candidate tasks rather than trying to
  load a nonexistent second task checkpoint.
- Final test report overwrite is refused; thresholds come from the frozen
  validation candidate.
- Offline model initialization disables unnecessary backbone downloads and
  reconstructs COCO v1 FrozenBatchNorm correctly before strict checkpoint load.
- Targeted regression suite: 22 passed, one inapplicable missing-Shapely test
  skipped after Shapely was installed. MPS detector forward/backward and a 3D
  convolution forward/backward passed synthetic compatibility checks.

## Reproducible runtime

Python 3.13 environment `backend/.venv`: Torch 2.14.1, torchvision 0.29.1,
Shapely 2.2.0, OpenCV headless 5.0.0.93, torchmetrics 1.9.0, pycocotools 2.0.11,
nibabel 5.4.2 and nnunetv2 2.8.1. Source environment was not downgraded.
Use `PYTORCH_ENABLE_MPS_FALLBACK=1` for MPS commands outside the sandbox.
The official detector weights are cached in `storage/torch_cache/`.

## Unresolved datasets

- ICA: source repository licence, intermediate mask semantics and patient mapping
  unresolved; masks remain lossless and unthresholded.
- DCA1: readable 134 pairs but reuse terms and patient grouping unresolved.
- Mendeley: CC BY 4.0 confirmed, but release-specific group/partition mapping is
  unresolved. All 8,325 BMP/XML pairs decoded and boxes checked. Source CSVs have
  7,492 train and 833 test frames; all share prefix `14`, 64 numeric group tokens
  occur in train, 63 in test, with 63 overlapping. Removing test-overlapping
  tokens leaves only 14 training frames from one token. This cannot support a
  defensible validation split. Tokens have not been asserted to be patient IDs.

## Follow-up

User explicitly approved automatic follow-through. Created active 20-minute
thread heartbeat `finish-corovision-model-training`. It must stay quiet on
unchanged/non-actionable state, recover completed exports, continue eligible
work safely, and notify only on completion/failure/required action. It may not
invent permissions, bypass quotas/locks or purchase compute.

Refresh reports with `backend/.venv/bin/python scripts/build_measured_training_results.py`.
That script imports a complete CRC-valid `corovision_stenosis_final_results.zip`
from Downloads when available, and summarizes saved ARCADE, CADICA and complete
303-volume MSD out-of-fold measurements. It never substitutes queued jobs for
measurements. Final reports must explicitly list any unresolved datasets.
