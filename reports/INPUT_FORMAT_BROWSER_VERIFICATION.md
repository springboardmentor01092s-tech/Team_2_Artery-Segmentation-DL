# Input-format and browser verification — 17 November 2026

## Automated support

| Workflow | Evidence | Result |
| --- | --- | --- |
| 2D PNG/JPEG | Decode, size, dimension and non-finite validation tests | PASS |
| 2D XA DICOM | Modality/frame/pixel-spacing/PHI checks | PASS where eligible |
| Corrupt/unsupported/invalid 2D | Explicit rejection tests | PASS |
| 3D DICOM series | Ordering, one-series identity, spacing/orientation and payload limits | PASS |
| Mixed series/patient | Rejected rather than merged | PASS |
| Missing/irregular spacing | Rejected or withheld with reason | PASS |
| NIfTI | Affine, orientation, spacing and millimetre-unit preservation | PASS |
| Oversized/corrupt volume | Explicit rejection | PASS |

The final full backend suite passed 329 tests with five opt-in external/model checks skipped. Frontend tests passed 20/20 and the production build completed successfully.

## Fresh browser status

On 17 November 2026 browser control was restored and fresh PNG, JPEG, eligible XA DICOM, direct CT DICOM-series and NIfTI journeys completed against the application-only working tree based on revision `f2ea58743af251706bc4d509e140321cf024bb18`.

| Format | Source SHA-256 | Case | Saved run | Result |
| --- | --- | --- | --- | --- |
| PNG | `748a2d4fcd2df8a11e5c1b836abbdf5201d21f75be808e0e71865ef8cda7bf55` | `FRESH-PNG-20261117-112439` | `ae72625c-1949-4dd0-b9c0-6c663325facd` | PASS: upload, validate, frozen inference, visualize, automatic abstention, save, refresh/reopen and export |
| JPEG | `8e9e12b2df25eb9ae8dfd761b59b6521e5d1f3a9c61955c18efba2a0006f57e1` | `FRESH-JPEG-20261117-1638` | `8a6e72c1-944e-457d-8383-5108bd10b8f5` | PASS: upload, validate, frozen inference, six evidence panels, safe automatic abstention, save and exact-run reopen after reload |
| Eligible XA DICOM | `9951c3bd41da76fc61515f2a4186416c4904588d3c939ca9c3ea53d7f0a1335f` | `FRESH-XA-DICOM-20261117-1639` | `d74e1154-9492-4f3c-8b29-5e326ce9e8b1` | PASS: DICOM validation, source spacing `0.2,0.2`, frozen inference, six evidence panels, save/reopen and repaired source-grid measurement reassessment |
| Direct CT DICOM series | 16 de-identified synthetic classic-CT slices, transport fixture only | `PUBLIC-CTA-CHECK-1f26ed` | `8e6025c1-ab36-40df-8e31-34f6fcd127b8` | PASS (engineering transport): direct multi-file selection, reconstruction, inference, three previews, explicit boundary-touch abstention and saved report; not coronary/scientific validation |
| NIfTI | Public de-identified CTACardio fixture (`CTACardio_original_hu.nii.gz`) | `PUBLIC-CTA-CHECK-1f26ed` | `75c30403-db57-42ee-b513-fecf4490a868` | PASS: upload reached 100%, geometry-validation status appeared, inference completed, three orthogonal previews rendered, saved measurement report completed, and the same run reopened after reload |

The PNG source and the `saved_artifacts/original.png` member in the Evidence ZIP have identical SHA-256 values. The run reopened after a full page reload with the same UUID. The application produced one candidate and correctly withheld an accepted severity because local vessel-boundary contrast was insufficient. Browser console warning/error inventory was empty on the saved report page.

## Remaining action

The intended application input-format browser matrix is complete for engineering acceptance. Preserve the PNG evidence under `reports/browser_acceptance_20261117/` and the exact run identifiers above. The synthetic direct-series fixture proves browser transport, reconstruction and software behavior only; independent real coronary CTA accuracy, clinical measurement validity and production acceptance remain outside this pass.

### Fresh NIfTI journey receipt

At 16:29:46 local time on 17 November 2026, the browser selected the public de-identified CTACardio NIfTI fixture in the saved CTA case. The application exposed the real upload-progress indicator at 100% and the distinct text `Upload complete. Validating source geometry…`. It then created run `75c30403`, changed it from `running` to `completed`, and displayed the source shape `512 × 512 × 321`, runtime `7.77 s`, `342` predicted coarse-grid voxels and three orthogonal overlay previews. After a full page reload, the same run remained selected and completed with identical displayed values. Browser console warning/error inventory was empty before reload.

This proves the current NIfTI upload/progress/geometry-validation/persistence journey. A subsequent saved-run report repair removed an empty-reference-window crash; the same run then returned `experimental_mask_geometry` with 25 extracted paths, zero candidates and 251.04 mm traced rather than remaining on a loading placeholder. It does not establish scientific accuracy, independent CTA measurement validity or clinical suitability.

### Fresh XA DICOM measurement repair receipt

The first saved XA-DICOM assessment exposed an internal source decoder defect because the saved-run measurement path attempted to open the retained `.dcm` with Pillow. The source-grid loader now uses the same DICOM modality-LUT, percentile-normalization and photometric-inversion rules as intake. A focused retained-DICOM regression test passes. Browser reassessment of exact run `d74e1154-9492-4f3c-8b29-5e326ce9e8b1` associated path `P3`, calculated exploratory source-mask widths `15.62 / 16.12 source px` and `3.13%`, then correctly abstained because vessel-boundary contrast was insufficient. This replaces the decoder failure with an evidence-based quality gate; it is not an accepted clinical grade.
