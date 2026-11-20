# COROVISION AI — MANDATORY CORRECTNESS, TRUTHFUL OUTPUT AND ALTERNATIVE IMPLEMENTATION POLICY
Apply these requirements to every remaining task across Milestones 1–4, model evaluation, measurement, severity, XAI, reporting and deployment.
PRIMARY RULE
Every permitted alternative must produce correct, traceable and reproducible results within its declared scope.

An alternative cannot be marked equivalent to the original method unless equivalence has actually been demonstrated against predefined acceptance criteria.

The goal is not to make every dashboard card show a number. The goal is to make the complete application work correctly and communicate what the actual evidence supports.
1. NO FALSE OR FABRICATED INFORMATION
Never fabricate or misrepresent any of the following. Preserve original inputs and record legitimate preprocessing, derived artifacts and reviewer corrections with their provenance:
- Medical images.
- Segmentation masks.
- Lesion predictions.
- Model confidence.
- Vessel measurements.
- Calibration.
- Severity percentages.
- Clinical grades.
- Dataset labels.
- Expert annotations.
- Model evaluation metrics.
- XAI attribution.
- Browser test results.
- Download verification results.
- Deployment status.
Every displayed result must originate from an identifiable calculation, stored artifact or authorized reviewer record.
2. MANDATORY PROVENANCE
For every analysis, preserve the applicable fields below. Record unavailable fields explicitly where they affect interpretation:
- Case ID.
- Source image/frame/volume ID.
- Source hash.
- Model ID.
- Checkpoint hash.
- Preprocessing version.
- Analysis run ID.
- Candidate ID.
- Measurement method and version.
- Geometry and units.
- Severity protocol/version.
- Quality result.
- Sensitivity or uncertainty information.
- Evidence classification.
- Report version.
- Review status.
Reject cross-case, cross-run and cross-candidate mismatches.
3. IMPLEMENTATION ALTERNATIVES
When the original method is unavailable:
1. Identify the missing dependency.
2. Determine whether another method can satisfy the same functional requirement.
3. Check data, model and interface compatibility.
4. Define numerical and functional acceptance tests before executing.
5. Implement the alternative without overwriting the original.
6. Run positive, negative and edge-case tests.
7. Compare against known truth or eligible references.
8. Record its limitations.
9. Integrate it into the existing UI and reporting workflow.
10. Mark the original requirement PASS only if the alternative satisfies its actual acceptance criteria.
Otherwise mark PARTIAL or BLOCKED.

Do not use a different acceptance standard just to make the project appear complete.
4. DATASET ALTERNATIVES
Use only legally eligible compatible data.

Verify:
- License.
- Dataset version.
- Annotation semantics.
- Patient grouping.
- Study grouping.
- Cross-dataset overlap.
- Checkpoint exposure.
- Image/mask alignment.
Never label exposed development data as an independent test cohort.
5. MEASUREMENT CORRECTNESS
For 2D:
- Use source-aligned lesion-local measurements.
- Identify suitable same-vessel references.
- Preserve MLD/RVD units.
- Require valid calibration before reporting millimetres.
- Calculate narrowing from actual eligible diameters.
- Reject invalid reference selections.
- Record quality and sensitivity.
For 3D:
- Respect original voxel spacing, orientation and affine.
- Use valid perpendicular lumen cross-sections.
- Apply bilateral local references where justified.
- Reject branch, taper and centerline ambiguity.
- Distinguish area from diameter narrowing.
- Preserve measurement versions and historical evidence.
Do not replace rejected measurements with global percentiles or synthetic expected values.
6. SEVERITY CORRECTNESS
Use only the explicitly active, versioned research protocol.

Grade only eligible measurements.

Keep detection confidence separate from narrowing.

Withhold a definitive category where quality or uncertainty makes it unsupported.

Do not infer normal anatomy from no detection.

Do not claim official patient-level CAD-RADS from an experimental 2D lesion-level protocol.
7. EXPLAINABILITY CORRECTNESS
Generate attribution from the actual selected checkpoint and prediction target.

Verify:
- Candidate identity.
- Spatial mapping.
- Faithfulness experiments.
- Perturbation baselines.
- Model-randomization sanity checks where valid.
Preserve failed tests.

A visible heatmap does not establish scientific faithfulness.
8. FALLBACK BEHAVIOR
If valid real inference cannot execute:
- Explain the exact missing checkpoint, format, resource or quality requirement.
- Keep the real case in an accurate failed/blocked state.
- Do not automatically replace real inference with synthetic outputs.
- Offer an explicitly separate synthetic demonstration, if available.
If measurement fails:
- Preserve real candidates and masks.
- Show exact abstention reasons.
- Show exploratory estimates only in a separately labelled area.
- Never report accepted severity without eligible evidence.
If export fails:
- Report the failure.
- Do not substitute a stale report from another run.
9. REPORT CONSISTENCY
Require agreement across:

Database → API → Frontend → PDF → CSV → JSON → Evidence ZIP.

Verify:
- Same case.
- Same image or volume.
- Same checkpoint.
- Same candidate.
- Same measurement.
- Same quality status.
- Same research severity.
- Same saved report version.
No unexplained numerical or identity mismatches are permitted.
10. AUTOMATIC VERIFICATION
For every completed engineering task:
- Run unit tests.
- Run integration tests.
- Run applicable API tests.
- Run browser tests where required.
- Validate errors and edge cases.
- Verify persistence.
- Verify exports.
- Record reproducible evidence.
A successful frontend build alone is insufficient.

A passed synthetic test alone does not prove real model or clinical performance.

An unexecuted test cannot be marked PASS.
11. SCIENTIFIC CLAIM CLASSIFICATION
Assign each metric, test or result an evidence classification that reflects its verified scope:
- LIVE_FROZEN_MODEL_INFERENCE
- PRESERVED_MODEL_EVIDENCE
- DEVELOPMENT_EVALUATION
- SYNTHETIC_KNOWN_TRUTH
- SOFTWARE_INTEGRATION_VERIFIED
- BROWSER_VERIFIED
- EXPLORATORY_RESEARCH_ESTIMATE
- INDEPENDENT_REFERENCE_EVALUATION
- CLINICALLY_VALIDATED
Do not elevate evidence between categories without the necessary evaluation.
12. AUTOMATIC ALTERNATIVE SEARCH
When a task is blocked:
- Search existing implementation and verified local assets first.
- Investigate compatible licensed alternatives.
- Evaluate their ability to meet original acceptance criteria.
- Implement and verify a suitable alternative when authorized.
- Document what it proves.
- Document what it cannot prove.
- Continue with another executable task.
Do not repeatedly ask the project owner for a new pending-task list.

Do not falsely mark blocked scientific requirements complete.
13. RELEASE GATES
Block the relevant release acceptance when:
- A result is linked to the wrong image/run/model.
- Accepted measurement is unsupported by actual geometry.
- Severity is generated from detector confidence.
- Synthetic results are presented as real inference.
- Independent validation is falsely claimed.
- Saved report fields disagree.
- Authorization allows cross-user case access.
- A required critical browser workflow remains untested.
- An alternative does not satisfy the original requirement.
Preserve actual negative results and abstentions.
14. FINAL ACCEPTANCE REPORT
For every alternative used, provide:

Original requirement.
Original method.
Why original method was unavailable.
Alternative method.
Evidence of functional correctness.
Tests executed.
Measured performance or errors.
Known limitations.
Acceptance criteria satisfied.
Acceptance criteria not satisfied.
Final status.
Next action.

Use PASS, PARTIAL, FAIL, BLOCKED or NOT_TESTED.

Do not claim a project is fully accepted while mandatory original criteria remain unsatisfied.
15. CONTINUOUS EXECUTION
After completing each task:
1. Verify correctness.
2. Update the evidence ledger.
3. Identify remaining authorized work.
4. Choose the highest-priority unblocked task.
5. Automatically continue.
Stop only when all authorized executable tasks are complete, all remaining tasks are genuinely blocked, or the active session's limits or a required authorization prevent further work.

Training remains paused.

Deployment, commits and pushes remain unauthorized without explicit approval.
