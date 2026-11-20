# Severity protocol registry

## Active protocol

No severity protocol is active. `STENOSIS_SEVERITY_PROTOCOL` was unset during verification on 10 November 2026. Consequently, a valid reviewed diameter reduction can be stored, but its category is `Indeterminate` / not assessable. This is intentional and prevents an undocumented five-class scheme from being presented as clinical grading.

## Registry contract

An eligible protocol is a versioned JSON document loaded from the configured local path and retained by SHA-256 in each new measurement record. It must contain:

- unique protocol ID and version;
- source/reference and approving research reviewer;
- `approved_for_research` status;
- measurement method;
- applicable modalities and anatomies;
- explicit exclusions;
- unique, contiguous bands partitioning 0 through 100.

The application has no default Normal/Mild/Moderate/Severe/Critical boundaries. A detector score is never accepted as a narrowing percentage. No-detection is not converted to Normal.

## Current candidates

| Candidate source | Eligible now | Reason |
|---|---:|---|
| Repository synthetic A/B fixture | No | Software-test fixture only; not a patient grading reference |
| CADICA source grades | No | Exact-frame compatibility, definition and checkpoint exposure remain unresolved |
| AngioCAD segment labels | No | Segment labels do not establish matched lesion-level QCA measurements |
| ACC/AHA or ESC clinical thresholds | No automatic use | They do not supply the repository's complete five-category research protocol and anatomical stenosis is not equivalent to functional significance |

Primary-source review on 10 November 2026 confirmed that CAD-RADS 2.0 defines CCTA categories (0%, 1-24%, 25-49%, 50-69%, 70-99%, and total occlusion), but it is a per-patient coronary CT angiography reporting system rather than CoroVision's per-lesion X-ray angiography workflow. The ACC/AHA revascularization material identifies clinically important ranges such as 40-69% intermediate visual stenosis and anatomy-specific 50%/70% criteria; it does not define the requested complete five-category research scheme. ESC guidance also separates anatomical disease from functional significance.

An inactive proposal is stored in `EXPERIMENTAL_FIVE_CATEGORY_PROTOCOL_PROPOSAL.json`. It is deliberately marked `proposed`, has no approver or approval date, and cannot be loaded by the grading engine. Its bands are for guide review and software planning only.

## Implementation identity

- `backend/app/narrowing.py`: SHA-256 `83ea07034d45a0cc9266b13654fd29ab290b12e0967ca4545edd77c2a19c8cce`
- Protocol documents are limited to 65,536 bytes and hashed before results are persisted.

