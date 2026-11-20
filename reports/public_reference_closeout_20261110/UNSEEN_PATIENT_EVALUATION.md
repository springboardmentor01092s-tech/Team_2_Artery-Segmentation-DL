# Unseen patient evaluation

The [CARDIAG intake receipt](../cardiag_intake_20261110/RECEIPT.json) records 645 samples, 122 groups and disjoint patient IDs across its listed splits. The [evaluation plan](../cardiag_intake_20261110/EVALUATION_PLAN.md) describes the remaining gates. Release grouping alone leaves prior checkpoint exposure unresolved.

Lock the eligible groups only after comparison with source, training, validation and tuning manifests for the [frozen checkpoints](DATASET_AND_CHECKPOINT_EXPOSURE_AUDIT.md). No unseen-patient score is available.
