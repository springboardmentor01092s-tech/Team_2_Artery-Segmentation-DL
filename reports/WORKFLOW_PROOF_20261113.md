# CoroVision import and upload-to-report proof — 13 November 2026

## Legacy import

- Source database: `artertry segmentation/application/artery.db`
- Final database: project-root `artery.db`
- Imported cases: `ARCADE-REAL-VAL-001`, `DEMO-INTEGRATED-SYNTHETIC`, `INTEGRATION-SYNTHETIC`
- Repeat import result: zero new rows; import is idempotent.
- Database foreign-key check: no violations.
- Legacy image rows were not imported because all six referenced original/processed files are absent. The cases remain draft and explicitly require re-upload.
- Original migration receipt: `storage/migration_backups/20261113T130525Z/receipt.json`
- Idempotency-check receipt: `storage/migration_backups/20261113T132311Z/receipt.json`

## Signed-in Chrome verification

Role: Demo Researcher / Medical Researcher.

### 2D XCA proof

- Case: `DEMO-DCA1-003-20261109`
- Image: `dca1-003.png`, source 300 × 300; processed preview 512 × 512.
- Saved run: `6f7660c2-651a-45ff-8604-c81de77b6e4f`
- Model: `corovision-preserved-2d-20261023`
- Saved outputs displayed: original, processed image, binary artery mask, segmentation overlay, centerline, boundary, artery probability, stenosis probability and run history.
- Segmentation record: 8,662 artery pixels and 2,405 stenosis-mask pixels.
- Vessel evidence: four saved paths; P1 minimum mask width 2.34 source px, maximum 12.68 source px, sampled extent 261.68 source px, 407 samples.
- Candidate evidence: C1 0.6291, C2 0.2955 and C3 0.2585 raw uncalibrated scores.
- Severity: the source-grid vessel-diameter workflow is displayed and automatically assessed for compatible saved runs. Narrowing/category are withheld when eligible local/reference evidence is unavailable.
- Reporting: report builder binds the selected case, image and run; three immutable prior versions are available. Original/overlay, vessel evidence, candidate evidence and human assessment sections are selectable.

### 3D CTA proof

- Case: `FRESH-3D-fdbe28`
- Saved run: `d0fbbf42-e090-4fb5-a586-65eaab605321`
- Model: `imagecas-coronary-unet3d-128-v1`
- Status: completed in 7.89 seconds.
- Source volume: 512 × 512 × 321 voxels.
- Displayed result: 342 predicted coarse-grid foreground voxels.
- Saved outputs displayed: RAS X/Y/Z slice overlays, 360-degree vessel viewer, source-grid mask, coarse probability volume and result JSON.
- Report exports displayed: 3D research JSON, stage CSV and research PDF.
- Downstream status is correct: segmentation requires review; vessel graph and 3D stenosis detection are unavailable; diameter and severity are not assessable. No 2D result is substituted into the 3D workflow.

This receipt verifies software workflow and saved evidence display, not clinical accuracy or diagnostic validity.
