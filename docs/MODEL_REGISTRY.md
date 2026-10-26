# Inference model registry and eligibility

The authoritative pinned release is ml/releases/corovision_20261023.json.

| Model | Architecture | Checkpoint SHA-256 | Recorded validation |
| --- | --- | --- | --- |
| Binary coronary artery | resnet34_unet | ea692f8c9c655791a44a340907629cda4e812138a6f15d93cdb2a45166177a7c | Mean image Dice 0.8272773138933874; 200 ARCADE images |
| ARCADE stenosis masks | maskrcnn_resnet50_fpn | f0bc898c95b6efdd53863d5a430fb4b850c2451b440c5a53b92a73e73c5be2e3 | Pooled union Dice 0.56439208772936; 200 ARCADE images |

512×512 coronary X-ray only. Artery threshold .5; stenosis score threshold .1,
mask threshold .5. Raw probabilities/scores are uncalibrated. Release readiness
means hash/dependency verification, not formal approval or clinical certification.
These are the existing preserved research baseline; this audit does not promote
them or a new candidate. Formal policy approval is a separate persisted workflow.

Drive selected_for_integration flags are historical package metadata, not approval.
Nine task packages / 12 indexed checkpoints are inventoried in
reports/connected_handoff_audit.json. Full bytes of non-selected checkpoints have
not been rehashed in this audit. Keep 3D/other-anatomy and box detectors separate.
Do not use rejected candidate weights, temperature studies or copied test metrics
to silently replace the two active baselines.

Training architecture/preprocessing sources stay on the drive. Application
adapters load pinned state dictionaries with weights_only=True; no uploaded path
or training code is executed. Exact source/config and artifact digests belong in
every imported evaluation and saved inference result.

## Separate 3D research integration

ImageCAS coronary CTA 128³ U-Net is now available through a separate explicit
research-only volume workflow. See [3D inference](3D_INFERENCE.md) for the pinned
checkpoint, exact preprocessing, geometry, permissions and verification limits.
It does not change the approved/pinned 2D model selection or enable 3D severity.
