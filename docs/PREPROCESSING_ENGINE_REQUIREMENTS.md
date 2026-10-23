# Medical image upload and preprocessing engine

Implemented 14 October 2026. Research software, not clinically validated.
Training remains paused at the user's request.

## Requirement coverage

| Requirement | Implementation |
|---|---|
| Image upload and validation | Authenticated, case-authorized 2D upload; type, size, dimensions, decoding, duplicates and identifying DICOM-tag checks |
| Format conversion | Supported raster, 2D DICOM/frame, PDF/page → lossless grayscale PNG; separate NIfTI/DICOM-series volume preparation |
| Resolution normalization and resizing | 2D aspect-preserving 512×512 padded canvas; explicit 3D target spacing, preserving physical voxel-centre extent and recording actual rounded spacing |
| Intensity normalization | DICOM modality LUT/rescale followed by percentile normalization; high-bit-depth raster normalization; volume percentile clipping to float32 [0,1]; 2D model-input normalization |
| Noise reduction | Optional 3×3 2D median / 3×3×3 volume median; off by default to avoid erasing fine vessels |
| Contrast enhancement | Optional clipped autocontrast for 2D / local histogram enhancement for volumes; off by default |
| ROI extraction | Explicit 2D box; explicit 3D voxel box with updated physical origin and aligned mask crop; no invented anatomical ROI |
| Slice selection | DICOM frame and PDF page in 2D UI; prepared NIfTI x/y/z slice in engine/CLI (axial in browser) |
| 2D/3D model input | Separate CHW slice and CZYX volume arrays; no automatic dispatch to the XCA model |
| Data augmentation | Seeded paired small rotations in existing 2D training helper; new paired small physical rigid 3D augmentation, train split only; masks use nearest-neighbour interpolation |
| Registration where required | Explicit reference triggers rigid mutual-information registration; transform and optimizer status exported, mandatory visual QC; no automatic registration of unrelated studies |
| Pixel/voxel spacing | Original files retained; source/processed geometry recorded, NIfTI direction/origin/spacing preserved, mask geometry checked; missing/invalid spacing never invented |

## Browser demonstration

1. Log in as a researcher and create/select a de-identified case.
2. For XCA, select images, Standard or Research options and optional ROI/frame/page;
   click **Validate and upload**, inspect the preview and expand **Preprocessing record**.
3. For a CTA case, use **3D volume preparation**. Select a de-identified `.nii` or
   `.nii.gz`; optional aligned categorical mask and fixed reference; target
   x,y,z spacing or leave blank to retain it; optional ROI and axial slice.
4. Click **Prepare and download volume**. Inspect the ZIP: byte-identical source
   files, prepared NIfTI, optional prepared mask/registration transform, CZYX array,
   selected CHW slice, PNG slice preview and JSON provenance/geometry record.
5. Preparation alone does not run a model or start training. Volume exports are
   downloaded, not added to the 2D case-image collection. Save the ZIP securely.

Browser volume limits: 50 MB per input, 32 million voxels per volume, scalar 3D
only, NIfTI spatial units explicitly millimetres. Researcher/admin only. Files
are handled in a temporary directory removed after export. No inference from
uploaded masks and no automatic training augmentation on evaluation cases.

## Offline volume preparation

Run from the project directory using the Python environment containing backend
requirements. The output directory must not already exist.

```sh
backend/.venv/bin/python scripts/prepare_research_volume.py source.nii.gz output/new_volume --spacing 1 1 1 --slice-index 20
backend/.venv/bin/python scripts/prepare_research_volume.py path/to/deidentified_dicom_series output/new_series
backend/.venv/bin/python scripts/prepare_research_volume.py source.nii.gz output/new_training_volume --mask labels.nii.gz --split train --augment-training-seed 42
```

Use `--reference fixed.nii.gz` only when registration is scientifically required.
ROI coordinates then refer to the fixed-reference grid. Use `--roi x y z w h d`,
`--denoise`, `--enhance`, or `--slice-axis 0|1|2` explicitly as required. Originals
are not modified; offline exports record original paths/checksums rather than
duplicating the entire source dataset.

## Limits and verification

Rigid registration cannot model all non-rigid motion and does not guarantee
anatomical alignment. DICOM series import requires one series, consistent
orientation and regular slice positions. Enhanced multi-frame 3D DICOM, 4D
time-series, irregular stacks and unknown NIfTI units are rejected rather than
silently converted. Browser DICOM-series/ZIP upload is not implemented; use the
offline importer. Automated tag checks are not complete de-identification;
operators must remove identifying metadata and burned-in text before upload.

Synthetic/API regression tests cover geometry, labels, ROI, resampling, slices,
registration execution/status, train-only augmentation, NIfTI units, DICOM-series
sorting/rescale/spacing, malformed input and unauthorized access, plus existing
2D uploads. They are engineering checks, not clinical or dataset-wide validation.
No claim of highest model accuracy follows from preprocessing completeness.

Verification: 29 upload/volume/geometry and dataset-pipeline regression tests passed; frontend
TypeScript and production build passed. Existing test-only short JWT secret
warnings and a frontend bundle-size advisory remain. Browser visual/end-to-end
verification of the newly added 3D form has not yet been performed.
