# Independent reference measurement protocol

## Scope

Collect lesion-specific minimum lumen diameter (MLD) and reference vessel diameter (RVD) independently of CoroVision. These are research measurements, not expert clinical QCA unless a qualified QCA process is separately documented.

## Pilot package

The local, non-publishable reviewer package is at `/Volumes/One Touch/execution_readiness_20261030/corovision_severity_reference_pilot_20261110`. It contains 20 ARCADE test frames, the original dataset annotation overlays, a candidate manifest and an unlocked Fiji/ImageJ worksheet. The package contains no CoroVision predictions.

All 43 intended package files are listed in `package_files.sha256`; verification passed. The images remain outside the Git checkout. Do not redistribute them until the applicable ARCADE terms are resolved: the challenge registration page states CC BY-NC-SA, while a later public mirror identifies CC0 and the local COCO license fields are blank.

## Reviewer procedure

1. Verify the original image hash against the manifest.
2. Open the original frame in Fiji/ImageJ and remain blinded to CoroVision output.
3. Use the dataset lesion annotation only to identify the target lesion.
4. Mark the local vessel direction and the perpendicular minimum-lumen cross-section.
5. Select a suitable disease-free reference segment using the declared rule and mark a perpendicular cross-section.
6. Record original-image coordinates, MLD, RVD and method/version.
7. Retain `source_px` unless valid image-plane calibration is independently documented.
8. Mark overlap, poor boundary visibility, foreshortening or unsuitable reference segments as uncertain/excluded.
9. Record reviewer/method identity and timestamp.
10. Set `independent_of_corovision=true` only if locations and widths were established without CoroVision predictions.
11. Submit the completed worksheet for validation; do not edit the candidate manifest or images.

Measurements use full precision. Percentage narrowing is calculated only after locking as `100 * (RVD - MLD) / RVD`. Display rounding never determines a category.

