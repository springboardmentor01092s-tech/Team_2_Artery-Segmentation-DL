# Application model artifacts

The current inference application requires three pinned research checkpoints:

| Model | Installation path | Contract |
| --- | --- | --- |
| ARCADE artery binary union | `models/trained_release/artery.pt` | 2D coronary X-ray; residual U-Net, 512 grid |
| ARCADE stenosis instance masks | `models/trained_release/stenosis.pt` | 2D coronary X-ray; Mask R-CNN; uncalibrated candidate scores |
| ImageCAS coronary vessels | `models/volume_release/imagecas128.pt` | 3D coronary CTA; original HU, canonical RAS, exact 128-grid transform |

Architecture, preprocessing and immutable hashes are in the existing release
JSON files under `ml/releases/`. Source code and release contracts travel with
the application; checkpoints stay outside Git.

## Install from an already downloaded Kaggle handoff

Run from the application root, using the configured backend Python environment:

```sh
python scripts/install_model_artifacts.py --source /absolute/path/to/full_handoff
python scripts/install_model_artifacts.py --check
python scripts/check_local.py
```

The handoff must retain its `trained_models/` hierarchy. The installer preflights
all missing source checksums before copying any model, never overwrites existing
models, verifies copied bytes, and does not copy datasets, notebooks, training
runners, optimizer states as separate files, credentials, databases or uploads.
An optional `--report /absolute/path/to/new-receipt.json` saves a new receipt and
refuses to overwrite existing evidence. `--check` is read-only.

The current local installation already contains all three exact pinned files;
see `reports/model_installation_check_20261026.json`. They came from the previously
downloaded, verified Kaggle/drive handoff; no replacement was necessary.

## Download verification on 26 October

Chrome successfully opened the original private Kaggle notebook
`mokshagnamannam/corovision-syntax-pretrained`, version 1, run 358786766. Its
`syntax_pretrained/models/best.pt` output is displayed as 99.9 MB. The fresh
download attempt did not return a completed browser download within 60 seconds.
Subsequent filesystem verification confirmed both `Downloads/results.zip`
(415,883,566 bytes) and `Downloads/best.zip` (99,899,039 bytes). Despite the
browser-event timeout, these transfers completed. `best.zip` is the raw PyTorch
checkpoint with a browser-assigned ZIP extension: its SHA-256 exactly matches
the pinned artery model. Do not extract its internal pickle/storage members.

`scripts/import_kaggle_model_bundle.py` staged seven required model/metadata
files from the output bundle under
`external_artifacts/kaggle_downloads_20261026/1f2d59e502dc6a25/`, with an archive
and per-file checksum receipt. Downloaded training scripts, bytecode, last/optimizer
checkpoint and test metrics are excluded from this application intake. The
active model is unchanged because it already has the same exact bytes.

Further stenosis, ImageCAS, anatomical and DCA bundle requests reached a Chrome
error page: `ERR_BLOCKED_BY_CLIENT` on Kaggle's `/code/svzip/` download route.
They are requested but not confirmed received. Do not bypass the browser block,
disable protections, or claim all task packages were freshly downloaded.

Subsequent user-completed transfers resolved most of this intake: nine model
bundles, containing 11 checkpoints, are now staged and hash-inventoried. Nine
checkpoints match the prior handoff exactly; two resumed 3D models have genuinely
different tensors and remain quarantined. See
`reports/KAGGLE_DOWNLOAD_INTAKE_20261026.md` for exact filenames and task mappings.
No new HepaticVessel bundle was received. No existing active model was replaced.

Other available task packages, newer experiments and rejected candidates are
not automatically activated. DCA, CADICA boxes/grades, anatomical artery
instances, aorta, hepatic vessels/tumours and ImageCAS-X have different target
or preprocessing contracts. Installing their files alone would not integrate
their inference into the coronary mask endpoints. They require separate
task-aware adapters and verification; no new integration is claimed here.

No retraining, production checkpoint substitution, dataset pooling, deployment
or Git push is performed by this workflow. These models remain research-only.
