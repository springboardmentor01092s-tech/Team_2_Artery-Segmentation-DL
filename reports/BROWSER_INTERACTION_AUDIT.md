# Browser interaction audit — 14 November 2026

Browser: connected Chrome against `http://127.0.0.1:5173` with the FastAPI service on port 8000.

| Interaction | Result | Evidence |
| --- | --- | --- |
| Open overview | PASS | Real counts, two saved studies, role tools and research limitations rendered. |
| Open saved 2D case | PASS | Case metadata, lifecycle, access area and exact saved analysis link rendered. |
| Open exact 2D run | PASS | URL retained case/image/run IDs; original, masks, paths, candidates, measurements and explanations rendered. |
| Open saved 3D run | PASS | Three saved slice directions, run/model identity, geometry, stages and export controls rendered. |
| Open report builder | PASS | Exact case/image/run source and seven immutable versions rendered. |
| Reopen saved report version | BLOCKED | Native-select automation bridge could not select an enabled option. |
| Download/reopen exports | NOT_STARTED | Requires successful report-version selection or saved snapshot creation. |
| Narrow viewport | NOT_STARTED | Viewport capability not completed in this audit slice. |

Browser verification here proves rendering and interaction behavior only. It does not prove segmentation accuracy, stenosis accuracy, clinical grading validity or XAI faithfulness.
