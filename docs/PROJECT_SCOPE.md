# CoroVision AI — Group 3 project scope

**Academic title:** CoroVision AI: An Explainable Deep Learning Platform for
Coronary Artery Segmentation, Vessel Structure Analysis, and Stenosis Detection

**Tagline:** See the vessels. Detect the narrowing. Understand the results.

## Objective

Build a research decision-support application for 2D coronary X-ray angiography
(XCA). The system will segment coronary artery regions, localize suspected
stenosis, visualize the evidence, and report measured performance on held-out
data. The output is not an autonomous diagnosis.

## Dataset and labels

- Primary data: ARCADE, extracted in `arcade/`.
- `syntax/`: 25 observed artery-region classes in the train split, category IDs
  1-25. The shared category dictionary also defines category 26, but this is
  not present in syntax annotations.
- `stenosis/`: lesion polygons and boxes using category ID 26.
- Each task contains 1,000 train, 200 validation, and 300 test 512×512 PNGs.
- Training and validation images are distinct across tasks. The test sets have
  123 byte-identical images in common, but do not assume all images are paired.
- Identical filenames occur in different splits. Use task, split, and filename
  together as a unique path.
- Hold test images aside until the final model evaluation.

## Milestone 1 (weeks 1-2)

Provide a documented architecture, database schema and wireframes, plus a
working frontend/backend that supports researcher registration and login,
de-identified case creation, PNG/JPEG/DICOM upload, validation, and a normalized
512×512 preview. This stage does not make clinical predictions.

An additional research baseline now trains two lightweight neural models from
ARCADE masks and displays artery/stenosis overlays for uploaded images. Its
validation scores and limits are documented in `docs/AI_ANALYSIS.md`. No
severity grade is inferred.

## Later milestones

1. Improve and compare artery segmentation models; extract vessel structures.
2. Improve stenosis localization and validate against expert annotations.
3. Add measurement and severity only where reference labels and calibration
   permit meaningful validation. A 2D projected image alone cannot establish
   clinical stenosis severity reliably.
4. Add explainability, reports, model versioning, deployment, and final testing.

## Data handling

Use only public or de-identified images. Case codes are pseudonyms; do not enter
patient names, birth dates, addresses, or identifying medical history in the
prototype. Uploaded content stays local in `storage/`, which is ignored by Git.
