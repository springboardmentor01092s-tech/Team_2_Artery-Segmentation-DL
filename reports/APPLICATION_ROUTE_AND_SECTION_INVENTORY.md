# Application route and section inventory

`APPLICATION_ROUTE_INVENTORY.json` records 112 FastAPI route decorators with methods, paths, source files, line numbers and handlers. It is a source inventory. Routers not mounted at runtime and public/private access rules require runtime reconciliation. Fifty-two TSX component files were discovered.

The SPA uses shared `/` navigation states rather than separate URLs for every module. `App.tsx` owns `overview`, `cases`, `uploads`, `analysis`, `reviews`, `models`, `reports`, `account`, `admin`, `permissions`, `access` and `audit`. `permissions.ts` restricts their visibility; server-side access remains authoritative. Query parameters bind case/image/run identities for supported image workflows.

| Screen | Subsections | Data and API dependencies | Component | Current browser state |
| --- | --- | --- | --- | --- |
| Overview | Counts, library, findings, tasks | Authorized cases, analytics, tasks | `OverviewPanel.tsx` | BROWSER_VERIFIED (14 Nov 2026) |
| Cases | Overview, assets, notes, history | Case CRUD, image/volume intake, access grants | `App.tsx`, `CaseWorkflow.tsx` | BROWSER_VERIFIED for saved 2D/3D cases (14 Nov 2026) |
| 2D analysis | Original, mask, contours, centerline, candidates, widths, grading | Selected image/run and protected artifact endpoints | `AnalysisWorkbench.tsx`, `StenosisMeasurements.tsx` | BROWSER_VERIFIED for saved run `4157543d` (14 Nov 2026) |
| 3D analysis | Run selection, slices, orbit rendering, geometry, export | Volume list, preview artifact, report endpoints | `VolumeInference.tsx`, `VolumeOrbit.tsx` | BROWSER_VERIFIED for saved run `d2c06ad4` (14 Nov 2026) |
| Models | Research progress, installed registry, reports, experiments | Analysis status/models, research progress, evaluation APIs | `ModelWorkspace.tsx` | BLOCKED |
| Reports | Selected case/image/run, immutable versions and downloads | Research-report and volume-report endpoints | `ReportsPage.tsx` | BROWSER_VERIFIED for rendering and saved-version inventory; native-select automation and download click remain pending |
| Reference collection | Provenance, endpoints, draft, CSV/JSON export | Local browser draft and reference import workflow | `/reference-measurement.html` | BLOCKED |
| Administration | Users, roles, operational permissions, audit | Admin APIs and action grants | `AdminPanel.tsx` | BLOCKED |

Loading, error, empty and success behavior is partly exercised by component code and API tests. No complete per-control responsive or keyboard acceptance is asserted. On 14 November 2026 a connected Chrome surface was available and the overview, saved-case workspace, saved 2D analysis, saved 3D analysis and report builder were inspected against the running local application. The browser bridge could not select a saved native `<select>` report option even though the DOM implementation leaves the control and options enabled; do not treat that automation limitation as an application pass or failure. Export downloads and smaller viewport checks remain pending.
