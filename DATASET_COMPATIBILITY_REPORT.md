# Dataset compatibility report — connected-drive audit

25 October 2026. Review required before any pooling or training configuration change.

## Verified scope

### Current local recheck

The raw-data drive `/Volumes/240gb` is not mounted during this follow-up. The copied
local evidence remains available. `scripts/audit_local_dataset_evidence.py` freshly
rehashed all 15 copied evidence files: **15/15 match**. It also recomputed sample-ID
intersections directly from the copied ImageCAS manifests, without reading test
pixels or changing splits. This is not a fresh raw-image deduplication, patient
identity or license audit. See `reports/local_dataset_evidence_audit.json`.

| ImageCAS split → ImageCAS-X split | Train | Validation | Test |
| --- | ---: | ---: | ---: |
| Train | 395 | 55 | 107 |
| Validation | 81 | 13 | 27 |
| Test | 84 | 12 | 26 |

These are shared case-ID counts, not a claim of newly verified pixel identity.
In particular, ImageCAS test → ImageCAS-X train contains **84 shared IDs**. The
variants cannot be described as independent external cohorts after cross-exposure.
Do not move protected cases into training to repair these overlaps retrospectively.

The detailed proposed experiment/adapters plan is in
`docs/PROPOSED_TASK_TRAINING_PLAN.md`. It is a proposal only; executable training
configurations and dataset pooling remain unchanged pending review.

The drive records nine trained task packages: **five 2D and four 3D**, not six independent 2D and three independent 3D datasets. ARCADE shares source images across annotation tasks; hepatic vessels and tumours share a cohort; ImageCAS-X overlaps ImageCAS. A separate local ICA_NJ_BinarySeg intake was subsequently identified as a candidate sixth 2D source; it is not an indexed trained package. Including that intake yields ten inventory records, not proof of ten independent cohorts.

15 audit/provenance files were independently rehashed against both the transfer manifest and dataset evidence hashes; all matched. Twelve indexed checkpoint files were found. Availability/manifest agreement is not approval, nor a fresh evaluation. Full raw-data deduplication and licenses were not independently re-run or cleared.

| Task package | Modality / anatomy | Annotation | Train / validation / test | Decision |
|---|---|---|---|---|
| syntax | 2D X-ray angiography; coronary arteries | anatomical instance polygons | 1000 / 200 / 300 | conditional pooling with DCA binary masks only; keep anatomical task separate |
| stenosis | 2D X-ray angiography; coronary lesions | stenosis instance polygons | 1000 / 200 / 300 | keep separate; no second audited compatible lesion-mask cohort |
| dca2d | 2D X-ray angiography; coronary vessels | binary pixel masks | 93 / 20 / 21 | conditional pooling with binary union of ARCADE artery categories |
| aorta128 | 3D CT; aorta | binary AI pseudo-label volume | 8 / 2 / 2 | keep separate; exclude48 geometry-mismatched pairs |
| hepatic128 | 3D CT; hepatic vessels and tumours | multiclass expert voxel labels | 218 / 38 / 46 | keep separate; report vessel and tumour independently |
| cadica_corrected | 2D X-ray angiography; coronary lesions | grade-labelled xyxy boxes | 4033 / 908 / 1185 | keep grade-aware task separate; conditional class-agnostic detection comparison with archive |
| stenosis_boxes | 2D X-ray angiography; coronary lesions | Pascal VOC/CSV boxes | 6625 / 874 / 826 | conditional detection pooling with CADICA only after lesion-definition and negative-frame audit |
| imagecas128 | 3D coronary CT angiography; coronary arteries | binary voxel labels | 700 / 150 / 150 | keep separate from ImageCAS-X pending joint subject/split reconciliation |
| imagecasx128 | 3D coronary CT angiography with shared ImageCAS CT; coronary anatomical union | multiclass source collapsed to binary union | 560 / 80 / 160 | keep separate; derived overlapping cohort is not external validation |

## Dataset-specific contracts

### ARCADE syntax

- Dimensions: {"prepared":null,"source_2d_sizes":[[512,512]],"native_shape_range":null,"status":"train COCO dimensions; split counts are raw source counts before trainer exclusions"}.
- Labels: [{"id":1,"name":"1","supercategory":""},{"id":2,"name":"2","supercategory":""},{"id":3,"name":"3","supercategory":""},{"id":4,"name":"4","supercategory":""},{"id":5,"name":"5","supercategory":""},{"id":6,"name":"6","supercategory":""},{"id":7,"name":"7","supercategory":""},{"id":8,"name":"8","supercategory":""},{"id":9,"name":"9","supercategory":""},{"id":10,"name":"9a","supercategory":""},{"id":11,"name":"10","supercategory":""},{"id":12,"name":"10a","supercategory":""},{"id":13,"name":"11","supercategory":""},{"id":14,"name":"12","supercategory":""},{"id":15,"name":"12a","supercategory":""},{"id":16,"name":"13","supercategory":""},{"id":17,"name":"14","supercategory":""},{"id":18,"name":"14a","supercategory":""},{"id":19,"name":"15","supercategory":""},{"id":20,"name":"16","supercategory":""},{"id":21,"name":"16a","supercategory":""},{"id":22,"name":"16b","supercategory":""},{"id":23,"name":"16c","supercategory":""},{"id":24,"name":"12b","supercategory":""},{"id":25,"name":"14b","supercategory":""},{"id":26,"name":"stenosis","supercategory":""}].
- Identifiers: patient/study mapping unverified.
- License: release/license compatibility not verified for pooled reuse; existing Kaggle metadata is not sufficient legal clearance.
- Preprocessing: preserve original loader geometry, decoding and normalization; no shared transform assumed.
- Class support: {"train":{"1":374,"2":375,"3":369,"4":303,"5":525,"6":537,"7":340,"8":310,"9":198,"10":70,"11":21,"12":1,"13":320,"14":61,"15":129,"16":305,"17":107,"18":49,"19":38,"20":232,"21":43,"22":48,"23":31,"24":63,"25":127},"val":{"1":66,"2":66,"3":66,"4":56,"5":130,"6":125,"7":77,"8":74,"9":50,"10":25,"11":21,"12":6,"13":70,"14":17,"15":27,"16":70,"17":20,"18":24,"19":3,"20":55,"21":13,"22":15,"23":16,"24":18,"25":58},"test":{"1":100,"2":100,"3":100,"4":92,"5":195,"6":188,"7":83,"8":80,"9":66,"10":35,"11":14,"13":119,"14":15,"15":23,"16":110,"17":67,"18":27,"19":11,"20":88,"21":24,"22":24,"23":25,"24":49,"25":37}}.
- Source evidence: artifacts/dataset_audit.json, trained_models/syntax/package.json.
- Decision: conditional pooling with DCA binary masks only; keep anatomical task separate. Pooling authorized: **no**.

### ARCADE stenosis

- Dimensions: {"prepared":null,"source_2d_sizes":[[512,512]],"native_shape_range":null,"status":"train COCO dimensions; split counts are raw source counts before trainer exclusions"}.
- Labels: [{"id":1,"name":"1","supercategory":""},{"id":2,"name":"2","supercategory":""},{"id":3,"name":"3","supercategory":""},{"id":4,"name":"4","supercategory":""},{"id":5,"name":"5","supercategory":""},{"id":6,"name":"6","supercategory":""},{"id":7,"name":"7","supercategory":""},{"id":8,"name":"8","supercategory":""},{"id":9,"name":"9","supercategory":""},{"id":10,"name":"9a","supercategory":""},{"id":11,"name":"10","supercategory":""},{"id":12,"name":"10a","supercategory":""},{"id":13,"name":"11","supercategory":""},{"id":14,"name":"12","supercategory":""},{"id":15,"name":"12a","supercategory":""},{"id":16,"name":"13","supercategory":""},{"id":17,"name":"14","supercategory":""},{"id":18,"name":"14a","supercategory":""},{"id":19,"name":"15","supercategory":""},{"id":20,"name":"16","supercategory":""},{"id":21,"name":"16a","supercategory":""},{"id":22,"name":"16b","supercategory":""},{"id":23,"name":"16c","supercategory":""},{"id":24,"name":"12b","supercategory":""},{"id":25,"name":"14b","supercategory":""},{"id":26,"name":"stenosis","supercategory":""}].
- Identifiers: patient/study mapping unverified.
- License: release/license compatibility not verified for pooled reuse; existing Kaggle metadata is not sufficient legal clearance.
- Preprocessing: preserve original loader geometry, decoding and normalization; no shared transform assumed.
- Class support: {"train":{"26":1625},"val":{"26":406},"test":{"26":386}}.
- Source evidence: artifacts/dataset_audit.json, trained_models/stenosis/package.json.
- Decision: keep separate; no second audited compatible lesion-mask cohort. Pooling authorized: **no**.

### DCA134

- Dimensions: {"prepared":null,"source_2d_sizes":[],"native_shape_range":null,"status":"manifest-derived; see source COCO image records for ARCADE sizes"}.
- Labels: {"0":"background","1":"artery"}.
- Identifiers: patient/study mapping unverified.
- License: release/license compatibility not verified for pooled reuse; existing Kaggle metadata is not sufficient legal clearance.
- Preprocessing: Selected CPU model native256 input, evaluation common512 padded grid; preserve aspect/padding and paired mask transforms. Patient mapping unknown..
- Class support: {"status":"exact voxel prevalence not recomputed; see task-specific count reports"}.
- Source evidence: processed/dca2d/manifest.json, trained_models/dca2d/package.json.
- Decision: conditional pooling with binary union of ARCADE artery categories. Pooling authorized: **no**.

### AortaSeg

- Dimensions: {"prepared":null,"source_2d_sizes":[],"native_shape_range":{"min":[512,512,510],"max":[512,512,1019]},"status":"manifest-derived; see source COCO image records for ARCADE sizes"}.
- Labels: {"0":"background","1":"aorta"}.
- Identifiers: case IDs; patient/study linkage beyond supplied case IDs unverified.
- License: release/license compatibility not verified for pooled reuse; existing Kaggle metadata is not sufficient legal clearance.
- Preprocessing: canonical RAS; full field of view resized to 128^3; CT clipped [-200,800] HU; mask nearest-neighbor.
- Class support: {"status":"exact voxel prevalence not recomputed; see task-specific count reports"}.
- Source evidence: processed/aorta128/manifest.json, trained_models/aorta128/package.json.
- Decision: keep separate; exclude48 geometry-mismatched pairs. Pooling authorized: **no**.

### MSD Task08 HepaticVessel

- Dimensions: {"prepared":[128,128,128],"source_2d_sizes":[],"native_shape_range":{"min":[512,512,24],"max":[512,512,181]},"status":"manifest-derived; see source COCO image records for ARCADE sizes"}.
- Labels: {"0":"background","1":"hepatic_vessel","2":"tumour"}.
- Identifiers: case IDs; patient/study linkage beyond supplied case IDs unverified.
- License: CC-BY-SA-4.0.
- Preprocessing: Full field of view resized to 128^3; original-resolution evaluation still required..
- Class support: {"status":"exact voxel prevalence not recomputed; see task-specific count reports"}.
- Source evidence: processed/hepatic128/manifest.json, trained_models/hepatic128/package.json.
- Decision: keep separate; report vessel and tumour independently. Pooling authorized: **no**.

### CADICA

- Dimensions: {"prepared":null,"source_2d_sizes":[[512,512]],"native_shape_range":null,"status":"manifest-derived; see source COCO image records for ARCADE sizes"}.
- Labels: ["p0_20","p100","p20_50","p50_70","p70_90","p90_98","p99"].
- Identifiers: supplied patient IDs and video IDs.
- License: release/license compatibility not verified for pooled reuse; existing Kaggle metadata is not sufficient legal clearance.
- Preprocessing: preserve original loader geometry, decoding and normalization; no shared transform assumed.
- Class support: {"train":{"p20_50":732,"p70_90":753,"p90_98":703,"p50_70":738,"p0_20":1231,"p99":22,"p100":56},"val":{"p0_20":280,"p20_50":145,"p70_90":64,"p90_98":128,"p50_70":197,"p99":41},"test":{"p0_20":433,"p90_98":99,"p70_90":76,"p20_50":251,"p50_70":64,"p100":148}}.
- Source evidence: processed/cadica_corrected/manifest.json, trained_models/cadica_corrected/package.json.
- Decision: keep grade-aware task separate; conditional class-agnostic detection comparison with archive. Pooling authorized: **no**.

### Stenosis archive

- Dimensions: {"prepared":null,"source_2d_sizes":[[512,512],[608,608],[800,800],[1000,1000]],"native_shape_range":null,"status":"manifest-derived; see source COCO image records for ARCADE sizes"}.
- Labels: ["Stenosis"].
- Identifiers: provisional filename groups, not verified patient IDs.
- License: release/license compatibility not verified for pooled reuse; existing Kaggle metadata is not sufficient legal clearance.
- Preprocessing: preserve original loader geometry, decoding and normalization; no shared transform assumed.
- Class support: {"train":{"Stenosis":6626},"val":{"Stenosis":874},"test":{"Stenosis":826}}.
- Source evidence: processed/stenosis_boxes/manifest.json, trained_models/stenosis_boxes/package.json.
- Decision: conditional detection pooling with CADICA only after lesion-definition and negative-frame audit. Pooling authorized: **no**.

### ImageCAS

- Dimensions: {"prepared":[128,128,128],"source_2d_sizes":[],"native_shape_range":{"min":[512,512,166],"max":[512,512,277]},"status":"manifest-derived; see source COCO image records for ARCADE sizes"}.
- Labels: {"0":"background","1":"coronary_artery"}.
- Identifiers: case IDs; patient/study linkage beyond supplied case IDs unverified.
- License: release/license compatibility not verified for pooled reuse; existing Kaggle metadata is not sufficient legal clearance.
- Preprocessing: Coarse full-field resize; original-resolution evaluation required..
- Class support: {"status":"exact voxel prevalence not recomputed; see task-specific count reports"}.
- Source evidence: processed/imagecas128/manifest.json, trained_models/imagecas128/package.json.
- Decision: keep separate from ImageCAS-X pending joint subject/split reconciliation. Pooling authorized: **no**.

### ImageCAS-X

- Dimensions: {"prepared":[128,128,128],"source_2d_sizes":[],"native_shape_range":{"min":[512,512,166],"max":[512,512,275]},"status":"manifest-derived; see source COCO image records for ARCADE sizes"}.
- Labels: {"0":"background","1":"coronary_artery"}.
- Identifiers: case IDs; patient/study linkage beyond supplied case IDs unverified.
- License: release/license compatibility not verified for pooled reuse; existing Kaggle metadata is not sufficient legal clearance.
- Preprocessing: Coarse full-field resize; original-resolution evaluation required..
- Class support: {"status":"exact voxel prevalence not recomputed; see task-specific count reports"}.
- Source evidence: processed/imagecasx128/manifest.json, trained_models/imagecasx128/package.json.
- Decision: keep separate; derived overlapping cohort is not external validation. Pooling authorized: **no**.

## Leakage and annotation blockers

### Approved source-only follow-up

The owner subsequently approved one ARCADE-only improvement experiment, not
dataset pooling. A fresh local audit decoded 2,400 processed ARCADE train/validation
image/mask pairs and found the stenosis train_218/val_155 duplicate. The historical
training audit already excludes 218.png; preserve that exclusion. Three lesion
training masks are empty and require annotation-completeness review, not automatic
healthy labels. No protected test pixels were decoded. The syntax-only technical
gate passed, but patient independence remains unverified.

A separate 32-update artery topology-loss candidate was trained and evaluated on
all 200 development-validation frames. Dice decreased from 0.827277314 to
0.826976523 and missed artery pixels increased; the candidate was rejected and
the installed baseline hash remains unchanged. This does not approve pooling or
establish a model-accuracy improvement. Detailed evidence is in the parent
workspace `reports/improvement_20261025/` and
`experiments/arcade_topology_pilot_20261025/` (weights remain Git-ignored).

### Additional local 2D intake: ICA_NJ_BinarySeg V1.0

A fresh read-only audit found **616 images and 616 paired masks**, all 512×512.
All 616 pairs match the existing intake manifest's image/mask byte hashes; image
byte hashes are unique within this local source. This is not a decoded
cross-dataset deduplication claim. No geometry mismatches were found.

- Modality/anatomy: invasive coronary X-ray angiography; vessel masks, not lesion
  masks, grade labels or anatomical instances.
- **122 masks contain intermediate grayscale values**. Keep original labels;
  do not silently threshold these into validated binary truth. The machine-readable
  audit includes raw mask intensity counts, not invented semantic prevalence.
- Patient mapping is unverified. Repeated filename prefixes do not establish
  patient identity. Current split is `unassigned_pending_verified_patient_groups`;
  no train/validation/test assignment was created.
- No license file was found at the downloaded repository root; this does not
  establish legal reuse rights. Confirm release-specific terms before training.
- No physical spacing is provided in the PNG manifest. Preserve image geometry,
  label provenance and an explicitly reviewed target conversion.
- Decision: **hold/exclude from active training and pooling** until licensing,
  patient mapping, mask semantics and cross-dataset duplicates are resolved.
  It may then be proposed for group A, not stenosis supervision.

Local source: parent workspace `data/external/ICA_NJ_BinarySeg/V1.0`; intake
manifest `data/processed/ica/manifest.csv`. Fresh checks are recorded in
`reports/local_dataset_evidence_audit.json`; no published-paper performance values
were imported as CoroVision model results.

Saved decoded-image audit reports 17,585 X-ray task records, 124 duplicate groups and 123 cross-task ARCADE groups. This is preserved audit evidence, not a fresh full decode/hash scan here. ARCADE/DCA patient linkage is unverified. CADICA records 42 patients with 29/6/7 splits, but archive filename groups are not verified patients. Archive validation contains reference boxes on all 874 frames: healthy-case specificity is unsupported.

ImageCAS/X case-ID intersections include ImageCAS test → X train (84), validation → X train (81), train → X validation (55) and train → X test (107). IDs/header agreement do not prove complete pixel identity. Neither is independent external validation after cross-exposure. Keep frozen splits and group aliases before any future pooling proposal.

Aorta has only 12 aligned pseudo-labelled pairs; 48 geometry-mismatched pairs remain excluded. Hepatic 0/background, 1/vessel, 2/tumour must stay separate. Hepatic HU contract in audited notes is [-200,400], not the aorta [-200,800] window. Missing exact foreground prevalence remains missing.

## Proposed task configurations — not activated

1. 2D artery: separate ARCADE binary-union and DCA adapters; conditional pooling only after license, annotation coverage, global duplicate and patient-identity checks. Keep anatomical instance head separate.
2. 2D stenosis masks: ARCADE lesion polygons only; no conversion of boxes into reference masks.
3. 2D localization: separate CADICA grade-aware and archive box adapters; class-agnostic pooling requires aligned lesion definitions and negative-frame audits.
4. 3D coronary: independent ImageCAS and ImageCAS-X adapters/configurations; pooling blocked by overlap/split/semantic issues.
5. Other-anatomy 3D: aorta pseudo-reference, hepatic vessel and hepatic tumour remain separate; cross-anatomy transfer needs explicit justification and review.

No datasets, splits, adapters or training settings were changed. Please review these decisions before authorizing training-configuration changes. Full machine-readable dimensions/labels/support/provenance are in reports/connected_handoff_audit.json. Source report: connected drive CoroVision_Full_20261024/workspace/DATASET_COMPATIBILITY_REPORT.md.
