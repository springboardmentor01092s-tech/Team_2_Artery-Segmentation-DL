# Image explanation and report panels

26 October 2026. Image Review (and its shared Severity Review workbench) and
Reports use the same run-bound gallery with seven labeled slots: original,
landmarks, centerline, boundary, processed input, binary artery mask and overlay.
Landmarks are explicitly unavailable: the screenshot is not evidence of saved
annotations. No reference illustration is used as a patient prediction.

The boundary endpoint computes an inner morphological contour from the selected
run's saved binary mask without changing that mask or rerunning inference.
Boundary and overlay captions distinguish prepared coordinates from source
coordinates. Original source formats that a browser cannot render show a missing
display message, not a substitute image. Each panel has a readable description.

Authenticated read-only routes:

- `/api/images/{image_id}/analyses/{event_id}/panels`
- `/api/images/{image_id}/analyses/{event_id}/panels/{kind}`

Both enforce case access and exact image/run association. Fixed panel kinds only;
no filesystem path can be supplied by the client. Existing prediction records
are unchanged. New research snapshots store the panel inventory. JSON preserves
it, CSV includes it, and PDF renders available panels with unavailable notices.
Historical snapshot JSON is not rewritten. The existing report unit/integration
tests verify JSON/CSV/PDF export and immutable report history.

Verification: production TypeScript/Vite build passed; 3 backend reporting/panel
tests passed; 14 frontend tests passed. Tests cover missing landmarks/artifacts,
unrelated-case and mismatched-run denial, unauthenticated requests, all export
formats and unchanged source-mask bytes. Browser verified the actual saved public
ARCADE run a67e848f-1a07-4caa-a0ed-db2407ab8e47 displays original, centerline,
boundary, processed, mask and overlay links, with landmarks unavailable.
Screenshot: `reports/image-panel-gallery.png`.

The pre-existing large JavaScript chunk warning remains. This change does not
implement the separately requested Gemini explanation service, train models,
invent annotations, establish accuracy or add automated clinical grading.
