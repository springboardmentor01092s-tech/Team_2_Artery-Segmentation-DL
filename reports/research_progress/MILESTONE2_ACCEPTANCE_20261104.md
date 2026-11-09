# Milestone 2 evidence review | 4 November 2026

**Decision:** acceptance pending. The preserved baseline has real application outputs and fresh API persistence evidence. Remote replay, a matched advanced-model comparison, independent geometry validation and patient-level exposure clearance remain open.

| Evidence area | Status | Evidence and remaining check |
|---|---|---|
| Remote training | BLOCKED_ACCESS | Historical application baseline `corovision-preserved-2d-20261023` has a saved executed event. The local trial ledger contains only submission/result records for rejected fixed-hole run 362745762 v1. No completed new replay bundle or paired U-Net/U-Net++ training receipt was located. Obtain the authorized run ID, notebook/input versions, logs, best/final checkpoint hashes and output manifest. |
| Inference replay | EVALUATION_PENDING | Existing demo includes a mask, overlay, boundary and centerline. The artery probability map and raw scores are retrievable from that saved event. A fresh Kaggle replay and output comparison remain pending. |
| Model comparison | EVALUATION_PENDING | The 29 October comparison report contains historical ARCADE results and 200 paired postprocessing rows. A U-Net vs U-Net++ evaluation on a fixed matched cohort remains pending. |
| API persistence and download | COMPLETE_VERIFIED | After server startup, two authenticated history reads matched the saved event, image, model and geometry. Six PNG panel responses matched saved bytes. Probability map, artery mask artifact and raw scores returned HTTP 200 with recorded hashes. Anonymous mask access returned HTTP 401. See the companion API receipt. |
| Browser integration | EVALUATION_PENDING | Visual rendering, refresh and user-facing download controls still require browser verification. Fresh upload and run creation were outside this read-only check. |
| Vessel geometry | IMPLEMENTED_NOT_VALIDATED | Saved centerline, branch geometry and approximate pixel widths are available. No matched expert diameter or centerline error was calculated. |
| Independent geometry reference | BLOCKED_MISSING_REFERENCE | Existing source review identifies candidate expert lumen annotations. No approved, calibrated, segment-matched independent reference for the evaluated cases was found. MAE and RMSE remain unavailable. |
| Patient/source independence | BLOCKED_PROVENANCE | ARCADE receipt verifies 1,000 metadata correspondences. Raster alignment and remote release binding remain open. DCA split reconciliation found 19 provider-test IDs exposed in historical training and three in validation. A de-identified patient/study mapping plus checkpoint exposure and duplicate checks is needed for an unseen-patient claim. |

Sources in this checkout are `SEGMENTATION_PROOF_20261029.md`, `../live_code_demo_aa0c852f/result.json`, `../segmentation_comparison_20261029/comparison.json` and `MILESTONE2_API_RECEIPT_20261104.json`. The research checkout holds the remote trial ledger, ARCADE correspondence receipt and DCA split reconciliation.

Next action: obtain the completed Kaggle replay bundle and verify its immutable versions, hashes and outputs before application import. Carry out browser verification against the imported run. Keep any independent geometry and patient-exposure conclusions separate until their evidence is available.
