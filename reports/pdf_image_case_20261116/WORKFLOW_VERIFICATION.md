# PDF Evidence Image — Workflow Verification

Date: 2026-11-16

## Identity and traceability

- Case code: `PDF-EVIDENCE-XCA-20261116`
- Case ID: `e25bce33-3c37-44f0-ac88-662dc610e694`
- Image ID: `71cb432e-d33d-4337-8385-25fc3f96b09b`
- Analysis run ID: `025d42ba-3c10-4c93-be09-17fe04decff9`
- Report ID: `03e78990-b81f-4a32-a254-8d3680404066`
- Source image SHA-256: `748a2d4fcd2df8a11e5c1b836abbdf5201d21f75be808e0e71865ef8cda7bf55`

The uploaded source is the 512 × 512 grayscale coronary angiography image included as `original.png` in the Milestone 3 evidence package.

## Completed workflow

1. Created a new XCA research case.
2. Uploaded the source evidence image.
3. Completed validation, exact-duplicate checking, grayscale conversion, model resize/padding, and lossless preview generation.
4. Ran the preserved model `corovision-preserved-2d-20261023` without training or changing its checkpoint.
5. Saved the analysis run and one detected candidate.
6. Ran the automatic measurement workflow and saved one traceable measurement record.
7. Generated report version 1.
8. Exported JSON, CSV, six-page PDF, and ZIP evidence bundle.
9. Reopened the case and analysis history successfully.
10. Validated the ZIP archive and PDF structure.

## Evidence panels

- Available: original image, processed image, centerline, vessel boundary, binary artery mask, and predicted segmentation overlay.
- Unavailable by design: human landmark/control-point annotation, because none was supplied and no annotation was fabricated.

## Measurement result and safety gate

The automatic cross-section measurement abstained because of low local vessel-boundary contrast. Therefore accepted minimum-lumen diameter, reference-vessel diameter, and clinical narrowing are unavailable. The system retained an explicitly exploratory mask-derived estimate (3.1258%, minimal) with evidence class `EXPLORATORY_RESEARCH_ESTIMATE`; it is not a clinically validated measurement.

Physical pixel spacing was not present in the source image, so dimensions cannot be reported in millimetres.

## Current state

- Processing: `completed`
- Case status: `analyzed`
- Workflow status: `pending_review`
- Report status: `draft`

All executable application workflow steps are complete. The remaining review/finalization action is intentionally human-only and must be performed by an authorized reviewer; this verification does not invent clinical metadata, annotations, approval, or validation.

## Integrity

- PDF SHA-256: `10f35497189713b5d5a652ed51f09ba4af3a012722dc2a051fac5fbfa7827ed2`
- ZIP SHA-256: `03332cb2fa784ba42240941990c2813241c8bfc205b91f60c63a1f764b0677e9`
- JSON SHA-256: `c117893f211a885affc89af11ce9a54cdf053959c5d8dd2bb125f67bc1723b4e`
- CSV SHA-256: `52047e576ec3def3b1f171b7f9923623f308c40ff3b2a110e41c6c5f1b666ab8`

