# Researcher protocol decision

The project owner is the research authority. No third-party guide signature is required for researcher-defined experimental functionality. Scientific evidence requirements remain separate from authorization.

## Proposed version for owner authorization

Protocol ID: `COROVISION_XCA_RESEARCH_5CLASS`

Version: `1.0.0-draft`

Authority: `researcher_defined`

Authorization status: `pending_owner_selection`

Validation status: `experimental_unvalidated`

Clinical use: `false`

| Full-precision diameter narrowing | Proposed output |
|---|---|
| Exactly 0% | Normal for the assessed segment only |
| Greater than 0%, less than 50% | Mild |
| 50% to less than 70% | Moderate |
| 70% to less than 90% | Severe |
| 90% to less than 100% | Critical |
| Exactly 100% | Separate suspected-occlusion assessment |
| Invalid or uncertain measurement | Indeterminate |

The merged lower-degree class and 90% boundary are experimental design choices. This mapping is not CAD-RADS and does not establish ischemia or clinical risk. Categories use the unrounded result. Exact-zero classification requires a trustworthy measurement with documented precision; lack of a detector candidate never establishes Normal. A zero-width prediction alone cannot establish occlusion.

The current contiguous-band engine cannot represent an exact-zero singleton or a separate 100% status correctly. This draft must remain inactive until endpoint semantics and their tests are implemented and the owner explicitly chooses the mapping.

## Current implementation correction

Measurement grading now checks configured modality and anatomy against the actual saved case/image. An incompatible protocol preserves the measurement calculation and withholds its category.

## Reference collection

The owner can create model-blinded manual research measurements using the existing 20-frame pilot. Record the actual annotator identity and method, retain source-pixel units, and freeze rows before comparison. These are researcher-generated references; observer independence and ARCADE checkpoint exposure remain limitations. Zero completed reference pairs currently support no numerical agreement claim.
