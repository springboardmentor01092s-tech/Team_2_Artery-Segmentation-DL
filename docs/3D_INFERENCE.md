# 3D coronary CTA inference — first integrated research model

## What is connected

The original ImageCAS 128³ 3D U-Net checkpoint executes locally on CPU. The
checkpoint SHA-256 is pinned in `ml/releases/imagecas_3d_128.json` and checked
before loading with PyTorch `weights_only=True`. No retraining, architecture
substitution, test-set tuning or baseline replacement was performed.

This is an explicit research-only integration, not clinical approval. Aorta,
hepatic, ImageCAS-X, MRA and 3D stenosis models are not silently substituted.

## Application workflow

1. Sign into a Researcher or Administrator account with case upload/analysis rights.
2. Create/select a coronary CTA case, choosing the 3D volume workflow.
3. Open Assets & preparation. Choose an original de-identified NIfTI file, at
   most 384 MiB on disk and 96 million native voxels with explicit millimetre units.
4. Confirm original Hounsfield-unit intensities and research-only use. These are
   operator attestations, not automatic modality or de-identification detection.
5. Run 3D segmentation. The saved job progresses queued → running → completed
   or failed. Refreshing the page retains history. At API restart interrupted
   jobs fail explicitly; they are not silently restarted or reported complete.
6. Inspect three saved canonical-RAS central slice previews. Download the binary
   source-grid mask, coarse probability NIfTI and structured result JSON.

Authorized case readers can view saved 3D history; starting jobs remains limited
to Researcher/Administrator upload and analysis permissions. Read authorization
is rechecked for every artifact. Paths are server-generated and artifact names
allowlisted. Original uploads are stored privately and not exposed by this API.

The generic preparation export remains a separate disclosure. Its percentile
normalization, enhancement, registration and ROI options are NOT applied to this
checkpoint. Upload the original CT, not that prepared/normalized export.

## Exact preprocessing and geometry

The original training code uses Nibabel canonical RAS arrays in XYZ order,
clips HU to [-200,800], resizes the full field to 128³ using SciPy linear zoom,
normalizes `(HU+200)/1000`, then stores float16 arrays. Inference preserves the
float16→float32 round-trip and XYZ tensor order. Outputs use two-class argmax.

SciPy's default `grid_mode=False` maps first/last voxel centres. The coarse affine
therefore uses `(canonical_shape-1)/127`, not `canonical_shape/128`. Nearest-neighbour
resampling restores categorical predictions to the original shape, affine and
qform/sform. The coarse probability volume retains its coarse physical grid.
No smoothing or connected-component filter is added without validation.

Restoring grid geometry does not restore native-resolution information. Fine
coronary branches may disappear at 128³. Scores are uncalibrated probabilities,
not diagnostic confidence. No physical diameter, narrowing, severity, reference
overlap metric or confirmed disease is inferred from this output.

## Installation and operation

Weights remain Git-ignored. The local checkpoint is
`models/volume_release/imagecas128.pt`; another laptop must provision the same
hash, or set `COROVISION_3D_CHECKPOINT` to that immutable local checkpoint.
Never accept arbitrary uploaded weights. The Docker configuration does not yet
provision this separate 3D release; deployment is deferred.

The local single-process dispatcher permits at most two accepted pending/running
3D jobs and executes one 3D model at a time. It is not a distributed durable queue.
Model tensors are loaded per job rather than retained permanently alongside 2D
models. Larger native volumes require a separately validated resource/patch contract.

API: authenticated `/api/volume-models`; case-scoped POST/GET
`/api/cases/{case_id}/volumes/analyses`; allowlisted artifacts below each run.

## Verification, 25 October 2026

### Native-volume compatibility fix and real public CTA acceptance

The first implementation's 32-million-voxel/50-MB limits rejected every native
ImageCAS shape recorded in the supplied manifest. The inference-only route now
streams uploads in 2-MiB chunks (384-MiB cap) and validates NIfTI geometry from the
header before voxel allocation (96-million-voxel cap). Heavy preparation runs once
inside the serialized job. Generic preparation and 2D limits are unchanged.
The exact trained normalization, interpolation and float16 round-trip are unchanged;
in-place clipping uses an owned array and never mutates the original.

3D Slicer's public CTACardio testing volume was downloaded from its official
hash-pinned distribution. Published SHA-256:
`3b0d4eb1a7d8ebb0c5a89cc0504640f76a030b4e869e33ff34c564c3d3b88ad2`.
Source: https://github.com/Slicer/Slicer/blob/main/Modules/Scripted/SampleData/SampleData.py
and https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/3b0d4eb1a7d8ebb0c5a89cc0504640f76a030b4e869e33ff34c564c3d3b88ad2 .

NRRD→NIfTI conversion preserved all voxel values, dimensions and physical
endpoints, with arbitrary text metadata omitted. The 512×512×321 native input
(84,148,224 voxels) completed live upload→checkpoint→artifacts in 8.002 seconds
inference time. All six artifacts were verified; the source-grid mask retained
shape/affine and the coarse probability grid was finite and in [0,1]. The model
predicted 342 coarse-grid foreground voxels. This number is not accuracy evidence.
The field of view/acquisition differs from ImageCAS; false positives/missed vessels
may occur. No reference mask, Dice calculation, clinical validation, retraining,
pooling or external upload was involved. Data stays Git-ignored and local, used
only for software acceptance, not redistributed as a training dataset.

Receipt: `reports/public_cta_integration_receipt.json`. Reproduction helper:
`scripts/verify_public_cta_workflow.py` (creates one acceptance case). The original
synthetic receipt below remains unchanged. A known source hash marks its UI as a
synthetic fixture and collapses its artificial slice previews by default; zero
predicted foreground is never presented as a normal/healthy result.

Current regression result: **96 backend passed, 3 opt-in skipped**. Frontend
production build passes. Sparse native-size header tests verify no voxel decoding
during admission; oversize headers, unknown units and upload-size limits reject.

### Earlier synthetic-only acceptance

- Backend suite: **93 passed, 3 skipped** (includes one opt-in 3D real-weight test).
- Opt-in actual checkpoint test: **1 passed**, 7.83 s test wall time.
- Frontend tests: **14 passed**; production build passed (existing bundle warning).
- Live upload→job→checkpoint→saved artifacts acceptance: completed in **4.761 s**
  inference time. Six artifacts verified, original shape/affine restored, finite
  probabilities in [0,1]. Receipt: `reports/volume_inference_receipt.json`.
- Fixture is an explicitly synthetic HU-like gradient, not patient data. Empty
  predicted foreground is preserved as zero, not rewritten as a healthy finding.
  This verifies execution and geometry only, not anatomical accuracy, generalization
  or clinical validity. Real de-identified CTA acceptance remains to be performed.

Reproduce contract/API tests from backend: `.venv/bin/python -m pytest tests/test_volume_inference.py -q`.
Opt in to installed weights with `CV_TEST_REAL_3D=1`. The live verification script
`scripts/verify_volume_workflow.py` deliberately creates one synthetic case using
private local demo credentials; it never prints credentials or exports tokens.
