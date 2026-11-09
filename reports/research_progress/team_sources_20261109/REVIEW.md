# Team research intake | 9 November 2026

## One Touch evidence

The attached drive contains the extracted Kaggle replay 365494240 v2 and U-Net++ training run 364600841 v7. Every listed file matched its archived SHA-256 on this laptop (459/459 replay files and 838/838 advanced run files). The original ZIP integrity is reported by the saved archive receipts. This intake checked the extracted bytes.

- Replay 365494240 reproduced all 200 saved masks and pixel counts, with zero maximum absolute probability difference. Dice was 0.8272773 and IoU was 0.7122207. The earlier isolated browser receipt records refresh followed by manual reopening of the same run for three cases, with matching mask and width-profile downloads. The receipt does not demonstrate automatic restoration in the current app.
- U-Net++ 364600841 completed 40 epochs and 20,000 updates. Dice was 0.7860897 versus 0.8272773 for the matched baseline. The candidate was rejected and its training history is preserved.
- ROI-head refinement 365244729 and classifier-only refinement 365885468 were rejected. Saved geometry run 365636956 contains case-bound width profiles in source pixels. Proposal audit 366216357 did not pass its mechanism gate.
- Independent clinical lumen measurement validation and unseen-patient performance remain open.

## Google Drive DCA/ICA handoff

The shared folder exposes two model checkpoints, epoch histories, metrics, per-case scores, and visualization folders. This intake downloaded both histories, the evaluation CSV and the metrics JSON. Checkpoint listings were inspected. Checkpoint bytes remain on Drive.

The 21-row-per-model CSV reproduces the displayed mean Dice to four decimal places: 0.7572 for baseline U-Net and 0.7595 for Attention ResUNet. Recall in the Drive metrics decreased from 0.8036 to 0.7669. The Kedar branch README reports different Dice values (0.7539 and 0.7699). Keep the two result sets separate until the team supplies an exact checkpoint, cohort and evaluator binding. Patient independence, compatibility with the retained CoroVision models, and the meaning of the DCA/ICA dataset label require source verification.

## GitHub branches

| Branch | Snapshot | Selected contribution |
|---|---|---|
| Kedar-muley | 3831284 | Baseline U-Net and Attention ResUNet, DCA preprocessing, training, evaluation and vessel analysis |
| Rishika-Nakirtha | 6b40845 | ARCADE SYNTAX and stenosis evaluation, post-processing and vessel extraction scripts |
| goutham-teja | cc68f5d | AortaSeg-60 3D CT code and diagnostic report. Patch and whole-volume results are separate metrics |
| sgharshitha | e01dbed | U-Net and Attention U-Net ARCADE results, consistent with the segmentation results in the earlier teammate ZIP |

Selected code and evidence are preserved for review in experiments/team_sources_20261109. The intake manifest records full source commits, paths and file hashes. The application exposes selected reports and receipts as research evidence through its existing access checks. Findings here describe recorded runs and artifact integrity.
