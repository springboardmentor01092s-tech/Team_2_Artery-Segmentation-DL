# CARDIAG evaluation plan

CARDIAG is a separate 2D coronary X-ray reference source. Keep its original train, validation and test lists intact. The release audit is recorded in [RECEIPT.json](RECEIPT.json). Use the published validation list for adapter development only. Reserve the published test list for a single eligible locked assessment after the adapter and scoring rules are approved.

## Scope and release gates

- Use Zenodo record 19958730. Match the declared archive checksum and exact split-list SHA-256 values from the intake. Bind each eligible case to its image, binary artery mask, narrowing mask, uncertainty mask and original coordinate geometry.
- Verify full patient and center grouping, content duplicates, cross-source overlap and the checkpoint's training and tuning exposure before describing the cohort as unseen. Use the original labels and record any excluded case and reason.
- Pin the existing artery and stenosis checkpoints and source contract from `ml/releases/corovision_20261023.json`. The app input is a 512-square prepared angiogram. Use an explicit transform for each source image and map predictions back to the reference grid. Validate geometry and record interpolation for labels and probabilities separately.
- Verify annotation completeness, label encoding and what empty narrowing masks mean before counting negatives. Agree how uncertainty masks affect denominators. A filename and dimensions establish a file association. Review is required to confirm reference alignment and meaning.
- Three validation samples passed a PNG header check. Each had a 512 × 512 grayscale angiogram and three 512 × 512 RGB mask files. Bind the channel encoding before converting masks. The publisher's data-card script renders positive narrowing pixels as stenosis overlays, which supports a regional reference interpretation. It does not define one-to-one lesion IDs or certify empty masks as reviewed negatives.

## Milestone 2 · Artery and structure

Compare the binary artery prediction with `binary.png` on the common image grid. Report Dice, IoU, precision and recall with per-image and patient-grouped summaries. Use clDice or centerline coverage as a **mask-derived** structure metric. Separate any reference-mask-derived width error in pixels from expert lumen measurements. Acquisition geometry and detector spacing do not supply lesion-linked calibrated QCA references.

## Milestone 3 · Candidate localization

Use `narrowings.png` as a regional reference only after reviewing its semantics and coverage. First report regional mask overlap. Report lesion-level sensitivity, false positives per image and missed lesions only if the reference supports a reviewed one-to-one lesion representation and matching rule. Lock the detector operating point before final evaluation. Separate uncertain frames and avoid inferring negatives from an empty file.

Clinical diameter, percentage narrowing and severity remain separate tasks requiring lesion-linked expert measurements, calibrated reference diameters and a reviewed grading protocol. CARDIAG labels can provide anatomical context for attribution review. Actual attribution and model faithfulness still require their own verified diagnostic.

## Execution

The intake reads archive metadata and split lists. The plan is pending reference review, exposure checks, immutable remote input binding, and fresh Kaggle quota, ledger and execution-lock checks. Record candidate results and acceptance decisions only after actual evaluation.
