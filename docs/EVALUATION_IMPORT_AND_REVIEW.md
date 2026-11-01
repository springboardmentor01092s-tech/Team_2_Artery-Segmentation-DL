# External evaluation import and independent research review

No training runs on the application laptop. Keep raw datasets, credentials and
patient identifiers out of bundles. Only authorized de-identified research material
may be imported into the shared research workspace.

## From the training laptop

1. Export an experiment JSON document matching the authenticated **Download import
   schema** action in Model Evaluation → Experiment Lab. The live schema is
   GET /api/evaluation/workspace/schema.
2. Supply exact architecture/version/checkpoint SHA-256, task, 2D/3D designation,
   dataset version, split and evaluation protocol. Never substitute an inference
   case for a reference-labelled evaluation sample.
3. Metrics need name, value (or null), unit, definition, aggregation and direction.
   Ratio metrics are bounded 0–1. Do not use one Dice number for multiple tasks.
4. Epoch history is an increasing list of {epoch, values}; values may include
   train_loss, validation_loss, validation_dice, learning_rate, etc. Missing values
   stay null. Best and early-stopping epochs must occur in the history.
5. Include dataset counts with separate units, annotation/class distributions,
   exclusions, audit notes and whether patient independence was actually verified.
   Class and annotation distributions must not imply mutually-exclusive categories
   unless the original annotations support that interpretation.
6. Samples use de-identified IDs (letters/numbers/underscore/dot/hyphen), metric
   summaries, optional error category, reference availability, notes and artifact
   layer mappings. Supported layers: original, reference, prediction, probability,
   overlay and difference. Boxes/matches can be rendered externally into bound
   overlay/difference layers; record their matching rules in the protocol.
7. Artifacts have key, format and data_base64. 2D uses PNG. 3D uses a numeric NPY
   array (no pickle), with slice axis first; spacing, 4×4 affine and coordinate_frame
   are required per sample. Keep all layers on the same geometry. The viewer shows
   slices without inventing a native-space reorientation.
8. Limits: 40 MB JSON, 30 artifacts, 1000 samples, 5000 epochs, 4,194,304 pixels/
   voxels per artifact; volume dimensions at most 256. Larger evaluations should
   export a documented review subset and aggregate metrics, not silently truncate.
9. Optional curves are named arrays of [x,y] pairs; explicitly identify metric,
   thresholds and protocol. Confusion matrix rows are actual classes and columns
   predicted classes, matching class_labels. No curves are synthesized from Dice.
10. Include configuration, code revision, seed, runtime, hardware and evaluated_at
    when recorded. Set deidentified_research_data=true only after checking the data.

An ML engineer or administrator chooses **Import experiment JSON**. Every import
gets a new immutable ID; importing the same version does not overwrite a baseline.
Image bytes are stored privately, not in ordinary report JSON. Artifacts require a
current authenticated research/model-management role. The workspace is shared among
those roles; do not import institution-restricted material without a separate scope.

## Acceptance policy and review

An administrator first creates a JSON policy using **Create acceptance policy**.
Policy fields: name, task, dataset (the exact Dataset schema), thresholds (metric
name and minimum/maximum), review_requirements. Policies are immutable and must
exist before the candidate import. A candidate references policy_id.

1. Importer submits an experimental candidate with notes → validation_pending.
2. Independent administrator inspects samples and saves individual sample reviews
   in Predictions. Importer-supplied reviewed flags are not approval evidence.
3. Administrator records visual and dataset/protocol review attestations and notes.
4. Server checks matching policy, metric thresholds, valid reference-bound samples,
   independent reviewer and persisted sample reviews before approving.
5. An administrator can reject a submitted candidate or retire an approved one.
   Decisions and sample reviews are append-only and appear in the audit trail.

Approval is research governance only. It does not deploy or replace checkpoints.
Live model activation remains a separate existing administrator workflow; preserved
release mode blocks legacy activation. Never treat approval as clinical validation.

## Data and graphs

- Training: recorded epoch traces, checkpoint markers, exact values in accessible
  tables. No inferred overfitting warnings.
- Comparison: same task/dimension/dataset/version/split/protocol and matching metric
  definitions/aggregation required; show differences and relative changes.
- Datasets: unit-labelled bar charts, annotation/class counts, exclusions and audit
  provenance. Overlapping datasets are never summed as independent samples.
- Predictions: original/reference/prediction panels, opacity/layer selection,
  zoom with scroll-to-pan, failure filter, next/previous sample and 3D slice controls.
- Errors: sample table, per-sample box summaries, imported PR/ROC traces and class
  confusion matrix when supplied. No unsupported lesion/centerline/severity metrics.
- Reports: authenticated JSON export includes immutable configuration, scores,
  sample metadata, review and checkpoint references, not raw artifact bytes.

## Deployment and tests

New SQLAlchemy tables are created idempotently by the application's existing
startup create_all: evaluation_experiments, evaluation_policies,
evaluation_decisions, evaluation_sample_reviews. Existing tables/checkpoints are
unchanged. Backup the database before upgrading an installation.

Tests use isolated temporary databases and labelled synthetic fixtures only.
No synthetic experiments are imported into the running application.

Actual external epoch logs, samples and acceptance policies are still required to
populate the workspace. Building an importer does not manufacture those results.
