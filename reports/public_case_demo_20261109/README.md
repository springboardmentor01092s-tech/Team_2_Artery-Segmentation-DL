# CoroVision real-case walkthrough

The 30-second recording joins two screen captures of the running application. The opening shows the actual new case, upload, preparation and inference submission. The remainder shows review of the same saved 2D run, exports, a separate saved 3D case, model evidence and settings.

| Approximate time | What to show |
| --- | --- |
| 00:00 | Demo researcher sign-in and research overview |
| 00:01 | Create a coronary research case with source provenance |
| 00:02 | Upload and prepare the DCA1 image |
| 00:03 | Start the combined analysis and wait for completion |
| 00:10 | Review the saved run, refresh, and switch among artery mask, centerline and localization |
| 00:15 | Inspect the explanation gallery and reviewed narrowing availability |
| 00:19 | Open the saved report and export PDF, CSV and JSON |
| 00:21 | Open the separate saved CTA, rotate the 3D preview, inspect slices and export its PDF |
| 00:25 | Model evaluation, research evidence and validation gaps |
| 00:28 | Profile and settings |

## Real 2D application run

DCA1 image 003 was selected from the One Touch copy of the public research dataset before inference. The PGM was converted losslessly to PNG for upload. The source and uploaded file SHA-256 hashes, exact checkpoint hashes, completed job, saved run, output hashes and report ID are recorded in [verification.json](verification.json). Dataset source context is available in the [DCA1 paper](https://doi.org/10.3390/app9245507).

The retained CoroVision release produced 8,662 artery-mask pixels, 2,405 stenosis-mask pixels and three candidate locations. The app restored the exact run after refresh. The evidence check downloaded the saved masks, centerline, overlay and other available artifacts. The shared local demo viewer has configured read access. An unauthenticated artifact request returned HTTP 401.

This is a fresh application case from a different named dataset than the recorded ARCADE development validation. Exact checkpoint patient exposure and publisher archive identity were not established. No accuracy metric, clinical severity or unseen-patient claim follows. The displayed pixel counts and locations are predictions. The narrowing panel remained unavailable without reviewed calibrated measurements.

## Separate 3D example

The CTA chapter reopens the existing public Slicer CTA run `d0fbbf42-e090-4fb5-a586-65eaab605321`. It verifies the 360° preview, three saved slices, source mask and PDF export. The CTA was processed in a prior application acceptance run. The walkthrough did not launch another CTA inference job.

## Exports

- [Walkthrough MP4](corovision-walkthrough.mp4)
- [2D report PDF](coronary-report.pdf) · [CSV](coronary-report.csv) · [JSON](coronary-report.json)
- [3D report PDF](volume-report.pdf)
- [Verification receipt](verification.json)
