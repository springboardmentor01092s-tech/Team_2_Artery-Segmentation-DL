# UI/UX audit — 14 November 2026

## Verified surfaces

Connected Chrome inspection covered the research overview, saved case navigation, a saved 2D angiography analysis, a saved 3D CTA analysis and the research report builder. These surfaces rendered real persisted records rather than placeholder metrics. The main navigation remained concise and role-scoped.

## Findings

| ID | Surface | Finding | Status | Evidence / next action |
| --- | --- | --- | --- | --- |
| UI-3D-001 | 3D explanation | The diameter/severity reason appeared once in a combined paragraph and again in the stage definition list. | FIXED | Removed the redundant paragraph in `frontend/src/VolumeInference.tsx`; rebuild and browser refresh required. |
| UI-REP-001 | Saved report selector | Seven versions render, but the browser automation bridge cannot operate the closed native select and exposes its options as disabled. Source options are enabled. | BLOCKED | Recheck manually or with a DOM-capable browser surface; do not classify as an application defect yet. |
| UI-RWD-001 | Responsive layout | Smaller viewport and horizontal-overflow acceptance is not yet recorded for all major workspaces. | NOT_STARTED | Verify overview, 2D viewer, 3D viewer, tables and report builder at supported narrow width. |
| UI-A11Y-001 | Keyboard controls | Semantic labels, headings, buttons and status regions are visible in the accessibility tree, but a complete keyboard traversal has not been executed. | PARTIALLY_IMPLEMENTED | Test focus order, disclosure controls, selects, candidate focus and downloads. |

## Positive observations

- Missing values are expressed as unavailable rather than zero.
- The 2D viewer keeps raw model scores separate from narrowing percentages.
- Uncalibrated 2D widths remain in source pixels.
- 3D diameter and area narrowing are presented separately.
- Experimental geometry, coarse-mask limitations, uncertainty and lack of reference validation remain visible.
- Report creation distinguishes the source for a new immutable version from an opened historical snapshot.

No clinical-accuracy or independent-validation claim is supported by this UI audit.
