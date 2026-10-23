# Free-GPU execution update — 14 October 2026

## Verified execution, not just prepared notebooks

Recovered the existing Colab session through Chrome's native accessibility
interface after browser-extension operations timed out. Colab showed:

- Connected free **Tesla T4**, 15 GB GPU memory, not subscribed, zero paid
  compute units. No paid service or new account was enabled.
- ARCADE syntax subprocess completed with return code 0. Its training report
  records 12 epochs, with validation-selected checkpoint and early stopping.
- Exported `corovision_syntax_results.zip` passed ZIP CRC validation. Checkpoint,
  comparison report and candidate metadata were extracted without replacing
  other experiments under `output/colab_runs/20261014_syntax/`.
- Submitted a new independent ARCADE stenosis training cell in the same runtime:
  Mask R-CNN ResNet50 FPN, maximum 25 epochs, patience 6, batch size 2, seed 42.
  It uses stenosis source labels and separate output directory, **not syntax
  checkpoint weights**. Execution was visible with approximately 2.5 GB GPU
  memory used. No finished stenosis metrics observed yet.
- Submitted the separate CADICA detector cell after stenosis. Public selected
  source-frame bundle upload was initiated, with a file entry visible in Colab.
  The queued code verifies exact SHA-256 and ZIP CRC before extraction/training.
  **Upload completion, integrity gate and CADICA training execution have not yet
  been observed.** It is not reported as training complete or running.

Live notebook (syntax results plus individually scoped queued experiments):
https://colab.research.google.com/drive/1Y7Wef_uZrYLuwYTW5bqjIngCBUJcXzA7

## Syntax validation measurements

From saved `models/individual/syntax/syntax/maskrcnn_resnet50_fpn/report.json`
inside the recovered output directory:

| Metric | Validation result |
|---|---:|
| Local ARCADE-style polygon task F1 | 0.156106 |
| Binary union-mask pixel Dice/F1 | 0.766379 |
| Binary union-mask IoU | 0.621244 |
| Binary union-mask precision | 0.772007 |
| Binary union-mask sensitivity | 0.760833 |
| Instance F1 at IoU 0.50 | 0.379358 |

The local challenge-rule implementation still needs cross-checking against the
official evaluator. Union Dice is supplementary and must not be substituted for
the primary anatomical task score. These results are not state-of-the-art, final
test scores or clinical validation. No automatic model promotion was performed.
The report states no test data used for training or selection in this experiment.

## ICA / DCA1 / Mendeley source investigations

**Mendeley:** release v3 explicitly states CC BY 4.0. This licence check is
resolved. The paper describes patient-series train/validation/test partitions
of 6660/833/832 frames. However, the downloaded release provides CSV membership
7492 train / 833 test frames, no separate validation CSV, and 63 overlapping
filename group candidates. Those tokens are not verified patient IDs. Therefore
the paper alone does not prove that the local CSV split is patient-independent.
Preserve CSVs/XMLs exactly and obtain a release-specific patient/series mapping
or partition clarification before deriving validation or asserting unbiased
patient-level evaluation. XML inclusive/exclusive coordinate convention also
needs explicit conversion documentation.

Sources:
- https://data.mendeley.com/datasets/ydrm75xywg/3
- https://www.nature.com/articles/s41598-021-87174-2

**ICA:** original README says binary labels but offers no clear dataset reuse
licence or released patient mapping. An existing unanswered issue asks the
authors exactly how the 616 released images map to the paper's 314 images / 99
patients. This corroborates the grouping uncertainty; it is not an author's
answer. Intermediate source mask values remain preserved; no threshold or
patient identifier was guessed. Training remains gated on source clarification.

Sources:
- https://github.com/MIILab-MTU/ICA_NJ_BinarySeg
- https://github.com/MIILab-MTU/ICA_NJ_BinarySeg/issues/1

**DCA1:** local 134 image/mask pairs are readable. Author landing page could not
be retrieved, and publisher endpoint returned rate limiting. The cited paper's
open-access licence is not treated as a licence for separately hosted patient
images. Local release provides no verified case-to-patient manifest. Reuse and
grouping remain unresolved, not falsely marked as prohibited or approved.

Author landing page:
http://personal.cimat.mx:8181/~ivan.cruz/DB_Angiograms.html
Original paper DOI: https://doi.org/10.3390/app9245507

## Free compute alternatives checked

Colab and Kaggle officially offer free GPU notebook execution, subject to quota
and availability. Existing Colab T4 was recovered, so no second service or login
was needed. Plugin-management discovery found no direct Colab/Kaggle execution
connector; it did not allocate a GPU. No credit-card trials, quota evasion,
account creation or Google-to-Kaggle SSO was attempted.

- https://research.google.com/colaboratory/faq.html
- https://www.kaggle.com/docs/notebooks

## Current human handoff

The native screenshot operation reported that the **Mac is locked**, and could
not unlock it automatically. User must unlock it manually before further UI
inspection, upload verification or new GPU job submission. Already submitted
cloud execution may continue, but its current progress is not assumed. Keep the
Colab session open; after unlocking, inspect stenosis and the pending CADICA
integrity gate and export checkpoints before session expiry.
