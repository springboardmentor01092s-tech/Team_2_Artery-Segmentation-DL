# Milestone3 data and annotation requirements

5November2026. Primary audit: `reports/milestone3/ANNOTATION_COMPATIBILITY_REPORT.md` and source hashes in its JSON companion in the shared workspace.

| Source | Supported task from audited labels | Prohibited substitution / outstanding gates |
|---|---|---|
| ARCADE syntax categories1–25 | Artery segmentation | Not stenosis severity; unknown patient/study groups and historical exposure must stay explicit |
| ARCADE stenosis category26 polygons/boxes | Binary lesion instance masks/detection | Source empty annotations are not automatically verified negatives; excluded train218 stays excluded |
| CADICA graded xywh boxes and source negative-video lists | Source-grade box localization/classification under compatible protocol | Not lumen masks/diameter pairs; no clinical severity mapping from arbitrary software bands |
| Stenosis archive XML/CSV boxes | Binary box detection after coordinate/rights/source review | No verified lesion masks; historical reconstructed grouping/splits are not official benchmark splits or verified patient IDs |
| DCA134 artery masks | Binary vessel segmentation only | Not a lesion detector or severity reference; original rights/exposure/alignment unresolved |
| DiGDA ARCADE relabels | Separate source-expert lesion grade/localization task after release/rights/split/exposure gates | Same ARCADE patients/images, not independent new patient evidence or continuous calibrated diameter measurements |

## Mandatory manifest

Source provider/release/license, task/anatomy/modality, original source key and SHA256, processed key and SHA256, transform/preprocessing version, reference annotation hash/format/class mapping, original split, study/patient group with provenance, source-negative semantics and all checkpoint training/validation/tuning exposures. Preserve original files/splits and rollback. No source is newly cleared for pooling or training.

CADICA latest source audit covers4033train/908developmentframes,5090boxes and1703source-negativeframes, with0issues and0patient-ID/exactbyte crosssplit overlap. Publisher release-byte identity and historical exposure remain unresolved; this audit is not independent evaluation. No new original source test annotation/image was opened.

For independent geometry, obtain same-frame/segment expert lumen masks and independently marked centerlines, their methodology and coordinate mapping. For narrowing, require independently reviewed comparable minimum/reference diameter pairs, their measurement locations, valid calibration evidence, reference selection and protocol/reviewer provenance. Keep unavailable results pending. Do not derive ground truth from the prediction or infer physical diameter from an uncalibrated PNG.

The current training freeze prohibits every optimizer/backpropagation run, including the predeclared RPN proposal. Existing frozen-model diagnostics remain Kaggle-only and require applicable explicit authorization plus fresh source/input/provider/account/jobs/debits/reserve/ledger gates; source compatibility alone is not execution clearance.
