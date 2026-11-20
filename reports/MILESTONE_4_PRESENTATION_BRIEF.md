# CoroVision AI final presentation brief

For the project review, present the implemented research workflow first and close with the conditions still needed for full acceptance.

| Slide | Main point | Evidence to show |
| --- | --- | --- |
| 1. CoroVision AI | Coronary vessel analysis research prototype | Project name and scope |
| 2. Foundation | Authorized case intake keeps preparation and run history traceable | [Architecture](../docs/ARCHITECTURE.md) and [input verification](INPUT_FORMAT_BROWSER_VERIFICATION.md) |
| 3. 2D angiography | Saved artery and stenosis outputs can be reopened with their original image | XA DICOM report v2, run `d74e1154`. Show original, overlay and the indeterminate assessment |
| 4. 3D coronary CTA | The saved volume analysis preserves geometry and reports when no candidate qualifies | CTA run `75c30403`. Show slice previews, 25 paths and the four-page PDF |
| 5. Model evidence | Development metrics use task-specific evaluation protocols | [Model selection](../docs/MODEL_SELECTION_20261113.md). Keep the artery, stenosis and CTA results in separate rows |
| 6. Reports and roles | Browser exports reconcile with their saved runs, and role navigation follows assigned work | [Export checks](REPORT_DOWNLOAD_CONSISTENCY.md) and the seven role walkthroughs in the [ledger](PROJECT_CONTINUATION_LEDGER.md) |
| 7. Acceptance and remaining work | Local research workflows have verified evidence. Full acceptance is partial | [Milestone closeout](MILESTONE_4_FINAL_ACCEPTANCE.md). Cover independent references, frozen-checkpoint validation, and deployment readiness |

Use the [live walkthrough](../docs/LOCAL_DEMO_RUN.md) for rehearsal. Populate slides with existing run-bound captures and preserve their labels. Keep the final deck private pending visual review.
