# Kaggle download intake — 26 October 2026

Nine completed model bundles were staged under
`external_artifacts/kaggle_downloads_20261026/`, containing 11 best checkpoints
plus their available configuration and validation metadata. Each archive and
extracted file has a SHA-256 receipt. Downloaded code was not executed.

| Download | Contents | Verification |
| --- | --- | --- |
| results.zip | ARCADE binary artery | Exact active artery checkpoint hash |
| results (1).zip | ImageCAS-X resume | Different weights; quarantined, not activated |
| results (2).zip | ARCADE stenosis, two Mask R-CNN architectures | Both match handoff; original FPN matches active stenosis model |
| results (3).zip | ImageCAS resume | Different weights; quarantined, not activated |
| results (4).zip | ARCADE anatomical instances, two architectures | Both match handoff; distinct from binary artery task |
| results (5).zip | DCA GPU512 | Matches handoff's unselected GPU candidate, not selected CPU baseline |
| results (7).zip | Aorta128 | Matches handoff; separate anatomy and pseudo-reference limitations retained |
| results (8).zip | CADICA corrected | Matches handoff; detection/grade targets not artery masks |
| results (9).zip | Stenosis boxes | Matches handoff; boxes are not reference lesion masks |

`results (6).zip` contains a DCA continuity experiment, not a baseline bundle.
It remains untouched in Downloads; its trained control/candidate files were not
imported into the application intake. Last/optimizer checkpoints, training
scripts, bytecode, test metrics and prediction arrays were not imported.
No incomplete Chrome downloads remained at the end of this check.

## The two different 3D files

Both were inspected with `torch.load(weights_only=True)` on CPU. Model state
keys match the corresponding baseline architecture, but the model tensors are
not identical:

- ImageCAS-X downloaded epoch 147 versus handoff epoch 97; downloaded SHA-256
  `858ab22c82e36258589f3c4d9056f380dfe9a5623a823bd3876deab96051b142`.
- ImageCAS downloaded epoch 124 versus pinned epoch 75; downloaded SHA-256
  `981c517acf6ac8a6875bd38770d61bf536c57b9f6d0819a51af8bc1672624dba`.

These are genuinely different checkpoints, not merely differently named or
repackaged copies. More epochs are not evidence of improved validation accuracy.
They remain staged pending matched evaluation. No gradients or inference were
run during the comparison; original checkpoint files were not changed.

## Application status and remaining scope

The currently integrated artery, stenosis-mask and original coronary 3D models
remain unchanged. New task packages are available in project staging, not
silently substituted into incompatible inference endpoints. Installing bytes
does not establish new task integration or accuracy.

No fresh HepaticVessel output bundle was among these downloads. Its previously
verified handoff package remains available separately; no fresh download is
claimed for it. The selected DCA CPU checkpoint also remains in the previous
handoff, distinct from the newly received GPU candidate.

Machine-readable inventory: `kaggle_download_reconciliation_20261026.json`.
For packages without an explicit selection field, that first inventory's
default `selected: false` means selection metadata was not supplied; it is not
a new rejection decision. The active-release contracts remain authoritative.

Verification: ten installer/archive-import tests passed. Models and download
staging are Git-ignored. No retraining, active-model replacement, deployment or
Git push occurred. Source ZIPs remain unchanged in Downloads.
