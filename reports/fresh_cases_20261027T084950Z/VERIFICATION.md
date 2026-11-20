# Fresh 2D and 3D application acceptance — 27 October 2026

User explicitly requested deleting all cases and uploading fresh 2D/3D cases.
Four prior active cases were soft-deleted through their owners' authenticated
API sessions. They remain recoverable through administrator trash; original
files, analyses and historical reports were not purged. `before.json` preserves
the inventory. The initial administrator deletion attempt returned 404 because
administrator role alone does not bypass case access; no permission was widened.
The corrected operation used each case owner's existing access.

Fresh cases:
- FRESH-2D-6a7902: public ARCADE development-exposed image 1, hash checked.
  Real installed artery/stenosis checkpoints executed, 4.47 seconds. Saved
  artery mask 8,927 pixels and stenosis mask 833 pixels; overlay and raw scores
  fetched successfully. Algorithmic vessel measurements and deterministic
  explanation present. A saved run-linked report exported as JSON, CSV and PDF.
- FRESH-3D-fdbe28: previously hash-verified public Slicer CTACardio NIfTI,
  native shape 512 x 512 x 321. Real installed ImageCAS checkpoint executed,
  7.89 seconds. All six artifacts fetched: source mask, coarse probability,
  three orthogonal overlays and result JSON. Binary source mask shape and affine
  match the upload. Probability volume is finite 128 cubed, bounded [0,1]. All
  three PNG overlays decode. Source mask has 13,728 predicted foreground voxels.

Chrome, signed in as Demo Clinician, visibly shows both fresh cases and their
completed saved results. Screenshots: `2d-workbench.png`, `3d-result.png`.
Database read-only check confirms only these two cases remain active.

## Not a claim that every project stage works

Neither sample supplies reference masks for this acceptance run: no accuracy,
unseen-generalization or clinical-validation claim. Severity remains blocked by
missing validated local/reference diameter protocol. Gemini is not integrated;
the explanation is deterministic. Attention/Grad-CAM and landmarks are correctly
unavailable. The 3D UI provides orthogonal previews, not interactive volumetric
reconstruction. A full 3D vessel/stenosis/severity/report workflow was not verified;
the verified 3D export is the saved result JSON plus NIfTI/PNG artifacts. The 2D
report export test does not establish 3D PDF/CSV support.

No research improvement, training, dataset pooling, checkpoint change or remote
upload occurred. This was explicitly requested local application acceptance.
See `receipt.json` for actual case/run IDs, stage states, artifact hashes and
model provenance. Secrets and session tokens are not recorded.
