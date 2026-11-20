# Measurement sensitivity protocol v1

For a nominal candidate with a unique candidate-crossing source-grid centerline path and eligible contrast, rerun the same cross-sections and reference-selection policy after one-source-pixel binary erosion and dilation. Keep the original image fixed and hold nominal contrast eligibility fixed for the two geometry-only perturbations. A displaced boundary is not a new independent image contrast test.

Retain each perturbed MLD/RVD, cross-section coordinates, reference selection, narrowing and abstention. The interval is the min/max of nominal and two perturbed narrowing values. The maximum deviation from nominal is passed to the experimental grade engine as a conservative symmetric sensitivity radius. Missing perturbed estimates cause abstention. This is a defined sensitivity range, not a confidence interval or real-image measurement-error bound.

Source-pixel masks are reconstructed only from the saved run's artery mask and inverse resize/ROI geometry. Masks from other runs are not substituted. The method executes no inference, optimizer, checkpoint mutation or model-buffer operation.

Clinical uncertainty, anatomical correspondence and true overlapping vessels cannot be established from binary mask topology alone. Stored association identifies a unique geometric path, not a clinically verified artery.
