# Preserved training models in the application

The `lingareddy-dhanush` branch connects two existing research baselines to the authenticated case-analysis workflow: a ResNet34 U-Net binary artery mask and an ARCADE Mask R-CNN ResNet50-FPN stenosis-mask model. The archive lesion-box detector is a separate task and is not rasterized into a fake lesion mask. Anatomical vessel instances, DCA and3DCT/CTA models remain separate tasks; no volume inference or calibrated patient confidence is activated.

Checkpoints and datasets are deliberately excluded from Git. Transfer `CoroVision_application_mask_models_v1.zip` separately, then run from the repository root:

```
python scripts/install_trained_release.py --install /path/to/CoroVision_application_mask_models_v1.zip
```

The installer checks the pinned release contract and both SHA256 hashes, rejects unexpected archive members and installs into ignored `models/trained_release/`. An existing differing installation is preserved rather than overwritten. This is the application-specific two-mask archive; the earlier three-model standalone research handoff is a different artifact.

To export on the training laptop:

```
python scripts/install_trained_release.py --export /path/to/CoroVision_application_mask_models_v1.zip --training-root /path/to/training-workspace
```

Install the backend and optional inference requirements in a compatible Python environment, then start the existing FastAPI backend and React frontend as described in README. Set JWT_SECRET privately. No external training service is needed at inference time. The adapter uses CPU/two threads and never downloads pretrained weights. Torch checkpoints are loaded with `weights_only=True` only after matching the release's fixed model hashes.

The Models page and authenticated `/api/analysis/status` expose the connected release, architectures, task-specific validation evidence and checkpoint hashes. Existing case permissions, retained source images, history and report routes remain in force. Run analysis from a prepared512×512coronary X-ray case. The artery path uses grayscale[0,1], internal ImageNet normalization, threshold0.5 and no additional median/autocontrast or morphology. Stenosis uses RGB[0,1], the original detector transform, score0.1/mask0.5 and the original contour filter. Optional user preprocessing changes the application input: benchmark scores are not per-image accuracy or validation of every enhancement/ROI.

Validation-only/development-exposed mask results: artery meanDice0.827277 on200images; ARCADE stenosis pooled unionDice0.564392 on200images. Their aggregation and task semantics differ. No historical test result is rebound to new weights. Rejected continuation candidates and ImageCAS/ImageCAS-X experimental temperatures are not installed. No detections do not establish a healthy case; mask widths are not clinically validated stenosis severity or blood flow.

To preserve artifacts but roll back routing, set `COROVISION_MODEL_PROVIDER=legacy` and restart the backend. Older registry activation is disabled while this release is configured so it cannot falsely report a switch while another provider still serves predictions.

Training does not complete application acceptance. Local parity/API checks and build results are recorded in `reports/trained_release_integration.md`; target-laptop Python/runtime and an actual end-to-end case test must also pass there. No local accounts, JWT secrets, uploads, databases, model files or archives should be pushed.
