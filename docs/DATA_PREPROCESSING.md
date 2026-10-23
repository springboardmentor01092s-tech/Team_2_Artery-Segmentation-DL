# ARCADE data preprocessing

This pipeline prepares the checked-in/extracted ARCADE release for academic
experiments without modifying its source files. It is not a clinically validated
diagnostic workflow.

## Observed source schema

The source root contains independent `syntax` and `stenosis` tasks, each with
official `train`, `val`, and `test` directories. Every split has PNG images and
one COCO-style JSON file. Images are referenced by `images[].id` and
`images[].file_name`. Annotations contain `image_id`, `category_id`, polygon
`segmentation`, `[x,y,width,height]` boxes, and area. Coordinates are image pixel
coordinates. `syntax` uses source category IDs 1–25; source category 26 is
`stenosis` and is used by the stenosis annotations.

The deterministic output is letterboxed to 512×512 grayscale. Images use
bilinear interpolation; masks use nearest-neighbor interpolation. Syntax masks
preserve source IDs with 0 as background. Stenosis retains per-image source COCO
annotations under `labels/` and additionally emits binary polygon masks under
`masks/` (0 background, 1 lesion). On-disk images remain uint8; scale to [0,1]
in model input code. Model-input preparation provides configurable 3×3 median
noise reduction and clipped autocontrast. These operations are deliberately
performed on load so the lossless deterministic image remains available for
ablation studies. Training-only seeded small-angle rotation is implemented with
nearest-neighbor mask interpolation.

ROI cropping accepts an explicit box and applies the identical crop to the mask.
The pipeline does not derive a model ROI from ground-truth polygons, because
that would leak labels during inference. Full-frame 512×512 images are therefore
the default model ROI.

## Run

```bash
python3 -m ml.preprocessing.run_preprocessing \
  --data-root arcade --output-root data/processed/arcade
```

Use `--dry-run` to validate without writing outputs. `--task`, `--split`, and
`--config` select subsets/configuration. Existing derived files are left in
place; `--force` explicitly regenerates them.

Generated reports include JSON inventory/environment/configuration, a complete
issue list, task CSV manifests with source SHA-256 values, and a QA contact
sheet. Official splits are never reassigned. Exact cross-split duplicates are
warnings requiring review, not silently removed. Empty annotations are retained
as valid negative images. Training-time augmentation must remain in the data
loader and apply only to training samples with identical geometry for image and
label.

## Validation and limitations

Run `python3 -m pytest tests/preprocessing -q`. The pipeline checks JSON shape,
references, category IDs, image readability and dimensions, polygon structure
and bounds, exact cross-split duplicates, mask geometry, and manifest mappings.
Exact hashes cannot detect near-duplicates or shared patients/angiography runs;
the release fields inspected here do not provide a verified patient grouping.
Polygon overlap in multiclass syntax masks is resolved in source annotation
order and should be reviewed if multiclass training is pursued.

The full local run processed 3,000 images (1,500 per task). It found no missing,
unreadable, malformed, unmapped, or out-of-bounds samples. It did find one exact
cross-split duplicate in the stenosis task: train image ID 218 and validation
image ID 155. This remains in its official split and is explicitly recorded in
`reports/issues.json`; experiments should disclose it and consider a sensitivity
analysis that excludes the validation copy.

## Dimensionality, registration, and spacing

ARCADE is an independent 2D X-ray angiography PNG dataset. It has no DICOM
series identifiers, ordered slices, physical pixel spacing, or voxel spacing in
its COCO records. Consequently, slice selection and 3D volume construction are
not applicable to the released data, and no defensible registration target is
defined. The library can stack explicitly ordered slices only when callers also
supply valid z/y/x spacing; it intentionally refuses to invent spacing.

Manifests record `spacing_status=unavailable_in_source_png_coco` and leave the
physical values empty. Uploaded DICOM images in the application retain
`PixelSpacing`/`ImagerPixelSpacing` separately, where present. See
`reports/pipeline_stages.json` for the machine-readable status of every requested
stage.
