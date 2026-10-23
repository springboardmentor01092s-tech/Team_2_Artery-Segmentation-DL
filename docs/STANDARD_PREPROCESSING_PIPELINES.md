# Standard 2D preprocessing presets

Upload image → Preprocessing profile. Standard, Noise Reduction, Contrast
Enhancement, and Noise + Contrast are peer choices in this single section.
There is no separate Standard pipeline selector.

| Preset | Additional operations before optional ROI and resize |
| --- | --- |
| Standard (default; API preset `baseline`) | None; existing validation/grayscale/high-bit-depth normalization |
| Noise Reduction | 3×3 median filter |
| Contrast Enhancement | Pillow autocontrast with 1% cutoff |
| Noise + Contrast | Median filter, then 1% clipped autocontrast |

All preserve the source, record available spacing and resize/padding geometry,
and produce a lossless 512×512 grayscale preview. Existing DICOM frame, PDF page
and explicit ROI selection remain supported. These presets are for the 2D case
uploader, not the separate NIfTI volume preparation workflow.

Enhanced presets can change thin vessels; they are not validated improvements to
the active model. The model's own input transformation still runs during inference,
so applying enhancement here can compound it. Compare with Standard, and inspect
the original before interpreting outputs. Constant or already high-contrast images
may look unchanged after an operation; that does not mean it was skipped.

The API validates the preset enum and rejects mixing a Standard preset with custom
Research options. Processing record version 2.2 stores the selected preset, effective
operations, hashes and warnings. The live UI pipeline path follows the selection.

Duplicate detection is now source-and-settings aware within a case. The same source
with a different preset/ROI/frame/page is retained as a separate prepared variant;
identical source/settings are rejected. Existing records use compatible default
settings for comparison. This pre-check is not a concurrency-safe database constraint.

Verification: frontend build and 29 selected API/preprocessing/workflow tests passed.
All four presets were checked pixel-for-pixel against their expected Pillow
operations on a synthetic image; source downloads and metadata were checked too.
No training or inference evaluation was started; no accuracy improvement is claimed.
