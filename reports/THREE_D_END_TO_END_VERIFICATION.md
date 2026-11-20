# 3D end-to-end verification — 16 November 2026

The public CTA case `PUBLIC-CTA-CHECK-1f26ed` reopens with correct modality, source/provenance and completed processing state. Automated tests cover NIfTI geometry, frozen job isolation, original-space artifacts, MPR previews, meshes, centerlines, disconnected components, perpendicular sections and report exports.

Known-truth cylinder sections agree with expected area within the declared tolerance and are invariant to tangent reversal. Empty, truncated, boundary-clipped and disconnected masks are handled explicitly without invented connections.

Limitations: experimental path-percentile reference selection, no quantified geometry uncertainty, no independent native-resolution lumen reference, and the current browser case-section navigation defect. Overall: **PARTIAL**.
