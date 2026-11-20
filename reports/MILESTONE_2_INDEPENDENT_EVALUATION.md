# Milestone 2 independent segmentation evaluation

## Executed exploratory DCA1 benchmark

Evaluated 129 of 134 publisher-release angiograms using the retained ResNet34 U-Net checkpoint, SHA-256 `ea692f8c9c655791a44a340907629cda4e812138a6f15d93cdb2a45166177a7c`. Used the existing 512×512 grayscale bilinear resize and padding path, sigmoid threshold 0.50, removal of recorded padding and nearest-neighbour resizing to the original grid. Reference foreground was the single nonzero value in strictly binary masks. Excluded Train PGM files 44, 66, 70, 73 and 79 for ambiguous multilevel masks.

- Mean image Dice **0.571798**.
- Mean image IoU **0.415585**.
- Aggregate pixel counts: TP 330,415, FP 159,939, FN 298,078.

This is exploratory external-dataset evidence. The benchmark pools eligible images across publisher folders and makes no patient-independence claim.

## ImageCAS-X exposure screening

Recovered the prepared ImageCAS manifest (700 train, 150 validation, 150 test IDs). Its SHA-256 `c3e7e891ae8a119a862b232706a175ab5d64e65e20c595d8b47e567d9e965693` matches the retained epoch-75 checkpoint's attention-trial binding. This establishes a concrete development grouping to screen. Before scoring, reconcile the ImageCAS-X subject IDs with this manifest and the retained checkpoint's original training and selection logs. Verify paired native-grid masks and images. The nominal test list alone does not establish exposure clearance. No 3D metrics were generated.

## Access decision

## Alternate paths

- **2D X-ray.** A publisher-bound DCA1 release is already staged under the workspace's `external_artifacts/dca1_mendeley_4wvf54td8d_v1_20261029`. Its intake lists 134 angiograms and annotations. Use this for a frozen external-dataset benchmark after checking case pairing and prior exposure. If patient independence cannot be established, report the result as exploratory. [Publisher release](https://data.mendeley.com/datasets/4wvf54td8d/1). XCAD is another candidate with 126 expert-masked test angiograms, subject to the same grouping and exposure checks. [XCAD source paper](https://openaccess.thecvf.com/content/ICCV2021/html/Ma_Self-Supervised_Vessel_Segmentation_via_Adversarial_Learning_ICCV_2021_paper.html).
- **3D CTA.** The older [Zenodo normal cohort](https://zenodo.org/records/4530387) also has restricted files. [ImageCAS-X](https://kitbransby.github.io/ImageCAS-X/) supplies detailed masks on existing ImageCAS scans. Evaluate only a subset proven absent from training, checkpoint selection and tuning for the retained ImageCAS model. Such a subset supports an unseen-patient result within ImageCAS. A different-source CTA cohort is needed to claim external generalization.

[UK Data Service study 855916](https://reshare.ukdataservice.ac.uk/855916/) lists both ASOCA archives as closed access. The depositor requires an explanation of intended use and written permission before release through UK Data Service. Local discovery located a saved catalogue page and no matching ASOCA archives in the searched project and execution-readiness inventory.

### Draft request for the project owner

**To** `asoca@unsw.edu.au`

**Subject** ASOCA data access for independent coronary CTA segmentation evaluation

Hello ASOCA data access team,

I am requesting access to the normal and diseased image and annotation archives for UK Data Service study 855916. Our CoroVision AI research project would use the paired CTA volumes and expert consensus masks to evaluate a frozen coronary artery segmentation model. We plan to assess overlap and surface agreement on native source grids and report aggregate results. Please let me know what project details, approvals, or data-use conditions you need to consider this request.

Thank you.

## Evaluation acceptance

1. Preserve approved dataset versions and file hashes. Pair each study with its expert reference and keep patient groups intact.
2. Reconcile the approved cohort against training, model selection and threshold-tuning manifests for the exact frozen checkpoint. Document any records whose exposure cannot be resolved and exclude them from the independent claim.
3. Verify source/reference dimensions, spacing, origin and direction. Preserve native grids for scoring and use nearest-neighbour resampling for categorical predictions when mapping them back. Record mismatches and inference failures by case.
4. Freeze preprocessing, weights, operating threshold and scoring rules. Report patient-level Dice and IoU with uncertainty. For CTA, include a physical surface-distance measure and the number of eligible, excluded and failed cases.
5. Treat the 2D X-ray evaluation as a separate cohort. The existing ARCADE development results and the CARDIAG grouping receipt do not establish prior-exposure clearance for a new 2D benchmark. See the [exposure audit](public_reference_closeout_20261110/DATASET_AND_CHECKPOINT_EXPOSURE_AUDIT.md).

## 20 November release metadata recheck

[ImageCAS-X v3](https://zenodo.org/records/23894668) is an open catalogue record for annotations on 800 existing ImageCAS CTA scans. The publisher lists `ImageCAS-X_dataset_v3.zip` at 934.1 MB with MD5 `4e7ec922065905fe29cc820276e6f283`. Version 3 corrects branch labelling in masks and centerlines. The checksum is publisher metadata and has yet to be verified on a downloaded archive. The [author repository](https://github.com/kitbransby/ImageCAS-X) documents the scan ID pairing and separate split lists. Its code license does not establish the dataset license. The inspected catalogue view did not expose a license value and archive preview returned HTTP 429. Keep downloads and scoring gated on verified data terms and the exact retained-checkpoint exposure audit. None of these catalogue checks establish independent scoring.

The [UK Data Service ASOCA catalogue](https://reshare.ukdataservice.ac.uk/855916/) still lists both archives as closed access and requires the data owner's permission. These release notes add a reproducible candidate identity. No protected data was opened.
