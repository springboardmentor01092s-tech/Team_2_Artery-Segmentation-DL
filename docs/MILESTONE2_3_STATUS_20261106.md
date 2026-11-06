# Milestones 2 and 3: implemented work and remaining evidence

Status as of 6 November 2026. Both milestones remain incomplete. Application functionality, synthetic tests, trained-model evaluation and independent clinical/reference validation are separate acceptance items.

## Delivered application behavior

- Saved case/image/run links pin the requested historical result. Missing or inaccessible evidence is not replaced with another image or a newer run. Leaving analysis, signing out or switching accounts clears the selection; stale responses cannot replace the current selection.
- Saved vessel contours, centerlines, candidate locations and path-linked width profiles can be displayed and downloaded with run/source lineage and ambiguity or unavailable flags.
- Missing stenosis masks are displayed as **Not saved** or **Not assessed**. A recorded zero remains zero. Reports preserve this distinction.
- CADICA source grades remain distinct from clinical severity. Operating points and unavailable attribution/faithfulness evidence are explicit.
- Candidate/path association and scalar-count evaluation helpers have synthetic software tests. These tests do not constitute clinical validation or authorize model activation.

Saved-output API evidence for cases 18 and 60 verifies exact identifiers, profiles, five artifact hashes per case and access denial across two client lifecycles. Earlier combined dashboard rendering and download proof exists. The latest automatic restoration implementation has logic tests, but its new browser refresh/download proof is still pending because supported browser control stopped at URL verification. No browser pass is claimed for that changed source.

## Actual research decisions

| Model or diagnostic | Result | Decision |
|---|---|---|
| Retained ResNet34 U-Net | Dice 0.8272773; IoU 0.7122207 | Baseline retained |
| U-Net++ 364600841 | Dice 0.7860897 | Rejected |
| Frozen baseline plus residual branch 365143415 | Dice 0.8279432; gain 0.00066586, recall/FN regression | Rejected |
| Retained Mask R-CNN ResNet50-FPN | 195 TP / 369 FP / 211 FN; F1 0.4020619 | Baseline retained |
| ROI-head refinement 365244729 | 206 TP / 383 FP / 200 FN; F1 0.4140704, gain below 0.02 | Rejected |
| Classifier-only refinement 365885468 | 196 TP / 375 FP / 210 FN; F1 0.4012282 | Rejected |
| Frozen proposal audit 366216357 | Top-1,000 IoU-0.5 box coverage 394/406; 12/211 mask misses lacked coverage | Missing-coverage mechanism screen failed; no training |

These are reused development results, not independent unseen-patient performance. The detector evaluator matches masks at IoU 0.5; do not relabel its F1 as box AP or patient classification accuracy. The preserved application score profile is separate from the frozen research score threshold 0.25.

The proposal audit verified all ten execution payloads, exact provider inputs, baseline parity and unchanged model/checkpoint state. The output archive passed CRC and member SHA checks. Provider closeout confirmed the draft OFF, zero active events and a two-minute displayed quota debit. No automatic activation or retry followed the diagnostic.

## Remaining acceptance evidence

1. Finish current-source browser restoration after refresh, exact saved-run selection, downloads and screenshots without bypassing browser access checks.
2. Obtain an eligible fixed independent cohort with publisher release identity, rights, patient/study relationships and complete checkpoint training/validation/tuning exposure. No pooled cohort is cleared.
3. Obtain same-frame expert lumen masks and centerlines, then evaluate overlap, boundary/centerline distances and lesion localization against the documented reference protocol.
4. Obtain valid calibration plus expert lesion/reference diameter pairs and a reviewed narrowing/severity protocol. Current widths are **source-pixel research estimates**, not validated clinical lumen diameters; clinical narrowing error and severity accuracy remain unavailable.
5. Execute the prepared eligible attribution diagnostic only after separate authorization and fresh execution gates. Actual attribution maps, sanity checks and faithfulness results remain pending. Probability overlays are not attribution validation.
6. Achieve an improvement that passes every frozen regression gate and reduces both false positives and missed lesions. No candidate has done so. The RPN-only training proposal remains held following its failed mechanism screen.

Training, fine-tuning, optimizer updates and backpropagation remain frozen. Research compute stays on the authorized free Kaggle account with the shared rolling budgets and single execution owner. This application publication does not authorize research execution, deployment or model activation. Credentials, patient uploads, databases, checkpoints and research execution notebooks are excluded from the publication.
