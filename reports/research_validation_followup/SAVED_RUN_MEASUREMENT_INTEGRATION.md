# Saved-run measurement integration

The automatic-measurement POST endpoint resolves case access, saved analysis, original image and run-named artery mask. It hashes available inputs and reconstructs the original source grid from the saved resize/ROI mapping. Invalid mappings abstain rather than substituting another image or rerunning inference.

`saved_measurement.py` reuses existing skeleton/path extraction. Exactly one open path with at least three samples crossing the candidate is required. Candidate-region mask components and nearby branch nodes are checked. The resulting association is a geometric correspondence, with `anatomical_identity_verified=false` and overlap limited to a mask-topology screen.

The associated path drives perpendicular cross-sections and nearest stable non-lesion reference-window selection in `local_diameters.py`. Candidate-local widths, source endpoints, reference cross-sections, input hashes and model provenance persist in a content-bound assessment file. Repeated identical assessments return the existing record. Human-reviewed records and historical inference results remain unchanged.

Successful synthetic API coverage creates a case/image/run, supplies its controlled mask, obtains approximately 50% narrowing, records two perturbations, saves/reopens the exact assessment and exports it in report CSV/PDF/ZIP. This uses an isolated stub inference fixture and makes no frozen-model accuracy claim. `test_automatic_measurement_pipeline.py` preserves the distinction.

Real Case 60 browser processing retained C1/C2/C3 and abstained for low contrast. Its exact saved assessment and v3 report IDs are recorded in `SAVED_RUN_BROWSER_RECEIPT.json`.

Known limitation discovered during integration: a candidate bbox that truncates the actual narrowed segment may choose a reference window on the same narrowed plateau. The controlled failure yielded 0% instead of the known 50%. The integrated path now withholds equal-width candidate/reference results with `reference_suitability_unconfirmed_equal_widths`. Other incomplete-coverage failures still require independent assessment; this gate does not certify disease-free reference segments.

Automatic protocol state is inactive by default. Explicit researcher/admin authorization records the actual actor and timestamp plus history. Modality/anatomy are enforced. Boundary sensitivity, not statistical confidence, is passed to the tested grade engine. No live owner authorization event was fabricated.
