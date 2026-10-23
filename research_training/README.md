# Preserved training sources

These four drivers are exact copies of the existing training workspace sources.
`source_manifest.json` records their original relative paths and SHA-256 hashes.
They are supplied for reproducibility, not launched by application setup or startup.
They do not represent all historical experiment runners or all model architectures.
The full training workspace and historical evidence require a separate transfer.

Use a separate Python training environment with compatible PyTorch, torchvision,
NumPy and Pillow; box detection additionally requires pycocotools. The application
environment is not a training dependency lock. GPU drivers and library builds must
be selected for the destination hardware. Some drivers require CUDA; pretrained
initialization may download public weights when no existing checkpoint is supplied.
Do not launch a historical driver solely to check an installation.

Inspect command options without starting training:

```bash
python research_training/train_segmentation.py --help
python research_training/train_pretrained_vessel.py --help
python research_training/train_volume_baseline.py --help
python research_training/train_boxes.py --help
```

For 2D drivers, supply `--root` pointing to the separately restored training
workspace, not this repository. It must retain the original `Dataset` and
`artifacts` directories, annotation files and split manifests. Never rely on the
segmentation driver's default root after relocating this source. The pretrained
vessel driver imports its preserved sibling `train_segmentation.py`.
For volume training, `--data` selects a prepared task directory containing the
original manifest and NPZ files. For box training, both `--root` and `--manifest`
are required. Inspect each manifest's class map and split before use.

Use a new output directory for an explicitly approved, bounded experiment.
Existing output directories may resume historical runs; never overwrite rollback
weights. These historical drivers do not implement provider watchdogs or a global
GPU quota guard. Do not use them as an unattended cloud queue.
Keep ImageCAS and ImageCAS-X separate, retain overlap disclosures, and exclude the
48 quarantined geometry-mismatched Aorta pairs. Preserve existing validation/test
roles. Do not invoke `--test` or treat development-exposed test data as untouched.

The live application's pinned artery and stenosis inference definitions and release
contract remain in the backend and `ml/releases`. These generic training drivers
are not a substitute for that inference contract. New checkpoints do not become
application models automatically: full matched validation, visual review,
compatibility checks, frozen acceptance gates and rollback retention are required.
Clone portability, model installation and second-computer runtime validation remain
separate checks; the presence of source does not certify them.
