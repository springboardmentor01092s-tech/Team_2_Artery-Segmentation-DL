# Stenosis and XAI continuation — 29 October 2026

## Outcome

No Kaggle job was launched and no model, metric, narrowing estimate or clinical
severity claim was created. The source-specific stenosis training gate remains
closed because this session cannot reverify the authorized Kaggle account,
active jobs, free resources or immutable remote input/notebook versions through
Chrome. The local ARCADE prototype config also still records an unverified
patient mapping, null label-mapping hash and pending preprocessing contract.
Authorization does not substitute for those facts.

DCA is not used as stenosis supervision. The traceable CC BY 4.0 intake resolves
the local byte-to-release link, but the provider archive split is 93/13/28 while
the checkpoint manifest is 93/20/21; 19 archive-test IDs occur in checkpoint
training and three in validation. Therefore the existing DCA members do not
support an untouched provider-test or independent-generalization claim.

## Application XAI integrity change

The existing attribution-only Grad-CAM implementation now upsamples to the exact
model-input spatial frame instead of a hard-coded 128-square frame. Saved result
metadata records method, target rule, layer, coordinate frame, mapping,
`weights_updated=false`, and lack of clinical validation. Unsupported adapters
remain explicitly unavailable. Attention-gate maps remain distinct from Grad-CAM.

Synthetic integrity tests hash every model state tensor before and after the
gradient calculation, verify evaluation mode, verify all parameter gradients are
cleared, verify the forward hook is removed, and verify a non-square 160x192
input produces a 160x192 attribution. This proves the tested software invariant;
it is not Kaggle attribution execution, faithfulness validation, clinical
validation or evidence about a patient image.

## Commands and results

- Initial `.venv/bin/python ...` attempt from the application root failed because
  that path does not exist. No tests ran.
- The next attempt found the backend environment but ran from the wrong directory
  and failed collection because `app` was not importable. No tests ran.
- Focused suite from `backend/`: 12 passed, one Starlette/httpx deprecation
  warning. The first run exposed a `bridge` versus `middle` provenance mismatch;
  it was corrected before the passing run.
- The first frontend build attempt ran from `backend/` and failed because that
  directory has no `package.json`.
- Production frontend build from `frontend/`: passed; 2,400 modules transformed.
  Vite retained its existing large-chunk warning.

## Remaining evidence gates

1. Chrome access capable of showing the signed-in `mokshagnamannam` identity,
   current free quota and zero/one active research job immediately before launch.
2. Immutable Kaggle dataset version and notebook version binding the exact ARCADE
   source images, category-26 annotations, split/exclusion manifest, baseline
   checkpoint and finite training code/config hashes.
3. Completed local source contract: authoritative license/version receipt,
   patient/study mapping or an explicit documented absence from the provider,
   label-mapping hash, duplicate/exposure audit, preprocessing, architecture,
   initialization, seed, stopping rule, 900-second watchdog, lesion IoU matching
   rule and predeclared baseline/regression gates. Preserve `218.png` exclusion
   and keep `738.png`/`888.png` uncertain rather than healthy.
4. For automatic narrowing: genuine reviewed candidate-local minimum/reference
   diameter pairs, same-frame calibration/spacing/projection provenance,
   reference-segment suitability labels and a predefined error protocol.
5. For severity: an authoritative task-appropriate protocol whose exact version
   is genuinely approved for research. Until supplied, grading remains not
   assessable.
6. For model-specific XAI validation: an eligible immutable Kaggle notebook/input
   version and predeclared finite cohort for sanity/faithfulness checks. No weight
   update or optimizer execution is permitted.

The existing reviewed-measurement workflow remains append-only and fail-closed;
no invented patient measurements were inserted. No model was promoted, activated,
deployed or pushed.
