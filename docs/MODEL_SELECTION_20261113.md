# CoroVision task-model and measurement selection — 13 November 2026

This application uses the strongest compatible, hash-pinned evidence available for each distinct task. Metrics from different tasks, dimensions and evaluation protocols are not pooled.

| Task | Selected artifact or method | Evidence used for selection | Decision |
|---|---|---|---|
| 3D coronary CTA segmentation | ImageCAS 3D U-Net, epoch 75, SHA-256 `b77271b1780f32100bc954ccbec2ac5c4efa54a10e0f5975b631924c8a2f553d` | Retained validation Dice 0.793693 and recall 0.787919 | Retained. The completed 39-epoch attention trial reached Dice 0.794519 but failed the minimum Dice-gain and no-recall-loss gates. |
| 2D coronary artery segmentation | ResNet34 U-Net release | Development validation Dice 0.827277 on 200 ARCADE images | Selected over the rejected attention candidate and Gharshitha U-Net test Dice 0.7597. |
| 2D stenosis localization/instance masks | Mask R-CNN release | Development validation Dice 0.564392 on 200 ARCADE images | Selected for candidate localization. Gharshitha U-Net test Dice 0.488805 remains supporting evidence, not the active detector. |
| Local/reference diameter and percentage narrowing | `sgharshitha-centerline-diameter-adaptation-v1` | S. Gharshitha’s centerline distance-transform width comparison is the primary source method | Selected as the main experimental measurement workflow, strengthened with source-grid cross-sections, unique-path association, branch exclusion, contrast checks, stable nearby references and boundary sensitivity. |
| Severity category | Versioned research protocol applied only after measurement gates | No independent clinical/QCA agreement cohort is available | Categories remain experimental and may be withheld. Detector confidence is never converted into narrowing or severity. |

The selected checkpoints remain research-only. Protected-test tuning, cross-source pooling, automatic checkpoint promotion and unsupported 3D stenosis/severity substitution are prohibited.
