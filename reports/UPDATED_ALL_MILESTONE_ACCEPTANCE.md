# Application acceptance ledger

## Existing verified behavior

- Shared authentication, case ownership and recoverable Trash.
- Fresh 2D source image upload, frozen segmentation, candidate localization and saved mask evidence.
- Experimental 2D mask-width narrowing and severity rules, with original stricter assessments retained.
- Fresh NIfTI CTA upload, pinned ImageCAS inference, physical geometry restoration, mask and probability exports.
- Separate volume history table and analysis viewer.
- Experimental Lee skeleton paths, physical EDT mask-width profiles and percentile narrowing candidates.
- Saved geometry cache bound to method version and mask SHA256.
- JSON and PDF geometry fields, candidate CSV rows and authenticated evidence ZIP implementation.

## Remaining implementation and acceptance work

- Perpendicular cross-sectional lumen contours, minimum and reference lumen areas, local reference suitability and geometric uncertainty.
- Synchronized interactive axial/sagittal/coronal source-volume navigation, window/level, CPR and selectable lesion overlays.
- DICOM reconstruction is present in generic preparation. Direct segmentation intake and its complete browser workflow still require verification.
- Model-specific volumetric attribution, controlled faithfulness experiments and sanity controls.
- Persistent reviewer geometry edits and complete run-selection URL restoration.
- Full browser verification of the new geometry cache and evidence ZIP, including identity and checksum reconciliation.
- Synthetic curved, anisotropic, branched and stenosed lumen tests for the new measurement method.
- Independent reference measurements, severity labels and exposure-cleared unseen cohort evaluation.

## Measurement scope

The current experimental volume method uses twice the physical distance to predicted-mask background voxel centres. Its reference is a path-interior percentile. It has no perpendicular cross-sectional lumen contour or area calculation. The candidates and categories must retain their experimental mask-geometry designation until a suitable cross-sectional implementation and its tests replace that method.

The attached 2D specification ends mid-sentence. Existing 2D functionality is retained while the explicit 3D requirements are implemented incrementally.
