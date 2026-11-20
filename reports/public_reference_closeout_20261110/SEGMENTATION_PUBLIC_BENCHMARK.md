# Segmentation public benchmark

The archived ARCADE replay used 200 development cases and returned mean Dice 0.8272773 and IoU 0.7122207. The archived U-Net++ comparison returned Dice 0.7860897 and was rejected. See [replay assessment](../research_progress/team_sources_20261109/milestone2_replay_run365494240_RESULT_ASSESSMENT.json) and [advanced assessment](../research_progress/team_sources_20261109/advanced_run364600841_RESULT_ASSESSMENT.json) for the saved run configuration and acceptance criteria.

New independent Dice, IoU and overlays are unavailable. Bind the original COCO references to the exact inference grids, resolve exposure, and freeze the evaluation cohort before a new Kaggle score. See [dataset audit](PUBLIC_REFERENCE_DATASET_AUDIT.md) and [checkpoint IDs](DATASET_AND_CHECKPOINT_EXPOSURE_AUDIT.md).
