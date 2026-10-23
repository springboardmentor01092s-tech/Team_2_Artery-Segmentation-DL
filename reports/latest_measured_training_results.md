# Measured training results

Updated UTC: 2026-10-14T10:30:58.787419+00:00

**All-dataset training is not complete.** Only persisted measured results are shown below.

| Experiment | Test images | Union Dice | Union IoU | Instance F1 (IoU .50) | Local ARCADE-style F1 |
|---|---:|---:|---:|---:|---:|
| ARCADE syntax | 300 | 0.7321 | 0.5775 | 0.3714 | 0.1331 |

Union-mask scores are supplementary binary vessel/lesion scores, not anatomical-class accuracy. These are research model evaluations, not clinical validation or evidence of highest possible performance.

## Remaining work

- CADICA: 2 training epochs persisted; final test evaluation pending.
- Local sequential queue: `waiting_existing_jobs`. CT model training is a separate pipeline.
- ICA and DCA1: source reuse/mask/grouping clarifications remain unresolved.
- Mendeley: CC BY 4.0 is confirmed. Excluding source-training frames with group tokens also in test leaves just 14 frames from one token; this cannot support a defensible train/validation split. No patient identifier or source mask interpretation was invented.

## Saved result artifacts

- ARCADE syntax: [test_report.json](</Users/lingareddydhanushkumar/Desktop/Codex/ML/Artery Segmentation and Stenosis Detection using Advanced Deep Learning Techniques /output/colab_runs/20261014_syntax/models/individual/syntax/test_report.json>).
