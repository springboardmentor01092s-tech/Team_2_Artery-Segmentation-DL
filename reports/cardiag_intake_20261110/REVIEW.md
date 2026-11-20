# CARDIAG dataset intake · 10 November 2026

The dataset curator confirmed a release count of 645 samples indexed 0–644, anonymized grouping identifiers and CC BY 4.0 licensing. To the curator's knowledge the release has no reference lumen diameters or QCA measurements. This note summarizes the correspondence. The original email stays private.

## What the archive confirms

The [publisher record](https://zenodo.org/records/19958730) identifies CARDIAG.zip, its 4,569,236,433-byte size, CC BY 4.0 and published MD5. HTTP range inspection read the ZIP directory and the three original split lists. The whole archive MD5 was recorded from the publisher. The archive was not downloaded in full.

| Published split | Sample IDs | Image, binary vessel, narrowing and uncertainty members present |
| --- | ---: | ---: |
| Training | 437 | 437 each |
| Validation | 60 | 60 each |
| Test | 148 | 148 each |
| Total | 645 | 645 each |

The original lists cover indices 000–644 with zero sample-ID overlap. There were no same-size, same-CRC image pairs in the directory. This is a preliminary exact-file screen. Pixel duplicates, transformed copies and cross-source overlap still require verification. One training entry has no catheter mask listed.

The JSON metadata exposes a record ID, patient ID and center ID. The sampled fields also include projection angles, keyframe index and acquisition geometry. The intake verified CRCs and all three grouping fields for **645 of 645 entries**, covering **122 distinct center–patient keys across nine centers**. The train, validation and test lists contain **80, 12 and 30** distinct center–patient keys respectively. Pairwise checks found **zero shared patient IDs, zero shared center–patient keys and zero shared record IDs** across the published splits. No patient identifiers are included in the receipt. The [publisher paper](https://arxiv.org/html/2607.22139v1) describes grouping by center and patient. The [publisher code](https://github.com/cvlab-ai/cardiag-benchmark/tree/1195c8f40d253e3611a30cd479d4b7486ccc3c23) reads the released split lists.

## Milestone use

- **M1 · Dataset intake.** The CARDIAG source, license, sample count, split-list hashes and reference-file inventory are documented. The grouping audit is complete within CARDIAG. Cross-source overlap and checkpoint exposure still need verification before an unseen-patient claim.
- **M2 · Vessel segmentation.** Binary vessel and uncertainty masks are reference candidates for overlap and mask-derived structure metrics. Three validation samples have matching 512 × 512 image and mask headers. Confirm pixel alignment and mask semantics before scoring.
- **M3 · Stenosis localization.** A narrowing mask is indexed for every sample. Verify which labels support a lesion-level match and how the release encodes uncertain and negative cases. Calibrated diameter, narrowing and severity still require independent expert measurements and grading evidence.
- **M4 · Traceability.** The dashboard links to this review, the machine-readable receipt and the evaluation plan. Raw masks, images, patient grouping values and private correspondence stay outside the application evidence.

The intake used the Zenodo record API, ZIP central directory byte ranges, CRC-checked split lists and CRC-checked JSON metadata. The first pass had connection failures. A full-archive download was stopped after a slow transfer. Bounded retries recovered every metadata member after the publisher returned HTTP 429 on some requests. The intake additionally checked CRCs for 12 PNG headers on three validation samples. No image or mask pixels were decoded, and no research model ran. Next, verify the full release digest and reference alignment, resolve checkpoint exposure and bind immutable inputs before a Kaggle evaluation.

[Machine-readable receipt](RECEIPT.json) · [Evaluation plan](EVALUATION_PLAN.md)
