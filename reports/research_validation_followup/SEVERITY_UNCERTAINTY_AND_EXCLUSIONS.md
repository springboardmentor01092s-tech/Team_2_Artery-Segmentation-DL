# Severity uncertainty and exclusions

The engine withholds a category when any required evidence is absent or invalid. `Indeterminate` is an assessment status, not a sixth grade.

| Condition | Behavior |
|---|---|
| Candidate exists but RVD is missing or unsuitable | Preserve candidate; no measured grade |
| Lumen boundaries not reviewed | Reject measurement |
| Image quality unacceptable | Reject measurement |
| Anatomy/reference ambiguous | Reject measurement |
| Missing/invalid calibration for millimetres | Reject physical measurement |
| Missing protocol | Save reviewed percentage; category indeterminate |
| Invalid/non-contiguous protocol bands | Reject protocol |
| Detector score available | Keep separate; never convert to narrowing |
| No candidate above threshold | Record no candidate; never auto-grade Normal |
| Learned and measured grades disagree | Both must remain separate and require review; fusion is not implemented |
| Unsupported modality/anatomy | Protocol applicability prevents supported grading |

Current exclusions include unreviewed automated MLD/RVD, global mask mean width as RVD, overlapping/ambiguous vessels, uncalibrated millimetre output, CADICA source grades as QCA, AngioCAD segment labels as lesion QCA, ischemia/flow claims and case-level worst-grade aggregation.

