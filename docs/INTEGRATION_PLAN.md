# Integration plan — review gates

1. Completed read-only drive inventory and metadata integrity check; review
   DATASET_COMPATIBILITY_REPORT.md before training adapter/config changes.
2. Match installed artery/stenosis bytes against handoff checkpoints. Do not copy
   duplicate weights or replace working application source from older backups.
3. Expose verified external epoch/sample records in the existing experiment
   importer. Preserve nulls, split and aggregation; mark imports experimental,
   not approved, unless actual authorized approval is recorded.
4. Correct or fail closed on input-contract differences, with resize/padding and
   inverse-coordinate tests. Keep optional enhancement experiments distinct.
5. Run real installed checkpoints on a de-identified or clearly labelled test
   fixture through upload, job worker, result persistence and artifact access.
6. Verify the UI displays those saved outputs; do not confuse a synthetic-input
   smoke test with scientific performance evaluation.
7. Connect additional 3D/detection models only after exact architecture,
   normalization, label, coordinate and approval contracts pass independently.
8. Severity remains blocked pending validated local/reference measurement protocol.
9. Remote Kaggle account mapping is optional for later artifact retrieval.
   No training, merge, publication or Kaggle run is authorized by this audit.

Await user review before any dataset pooling or training-configuration changes.
