# Milestone3 API reference

5November2026. Routes extracted from the actual `backend/app/main.py` AST; inventory is source inspection, not proof every route was runtime-tested. The application also has separately mounted routers; this is not a claim of exhaustive global API inventory.

| Method | Actual path | Handler |
|---|---|---|
| POST | `/api/cases/{case_id}/review` | `add_clinical_review` |
| GET | `/api/cases/{case_id}/reviews` | `list_clinical_reviews` |
| POST | `/api/cases/{case_id}/volumes/analyses` | `create_volume_analysis` |
| GET | `/api/cases/{case_id}/volumes/analyses` | `list_volume_analyses` |
| GET | `/api/cases/{case_id}/volumes/analyses/{run_id}/artifacts/{name}` | `volume_artifact` |
| GET | `/api/cases/{case_id}/volumes/analyses/{run_id}/report/{format}` | `volume_research_report` |
| POST | `/api/images/{image_id}/analysis/jobs` | `create_analysis_job` |
| GET | `/api/analysis/jobs/{job_id}` | `get_analysis_job` |
| GET | `/api/analysis/jobs/{job_id}/result` | `get_analysis_job_result` |
| GET | `/api/images/{image_id}/analysis/jobs` | `image_analysis_jobs` |
| GET | `/api/images/{image_id}/analyses` | `analysis_history` |
| GET | `/api/cases/{case_id}/analyses` | `case_analysis_history` |
| GET | `/api/images/{image_id}/analyses/{event_id}/overlay` | `history_overlay` |
| GET | `/api/images/{image_id}/analyses/{event_id}/artifacts/{kind}` | `result_artifact` |
| GET | `/api/images/{image_id}/analyses/{event_id}/panels` | `image_panel_inventory` |
| GET | `/api/images/{image_id}/analyses/{event_id}/panels/{kind}` | `image_panel_artifact` |
| GET | `/api/images/{image_id}/analyses/{event_id}/map/{kind}` | `history_explanation_map` |
| POST | `/api/cases/{case_id}/stenosis-measurements` | `record_stenosis_measurement` |
| GET | `/api/cases/{case_id}/stenosis-measurements` | `list_stenosis_measurements` |
| POST | `/api/cases/{case_id}/research-reports` | `create_research_report` |
| GET | `/api/cases/{case_id}/research-reports` | `list_research_reports` |
| GET | `/api/cases/{case_id}/research-reports/{report_id}` | `get_research_report` |
| GET | `/api/cases/{case_id}/research-reports/{report_id}/export/{format}` | `export_research_report` |

## Data contracts and authorization

- Read candidates, coordinates, model evidence and width profiles from the selected saved analysis result; there is no invented standalone candidate endpoint. Keep source/prepared coordinates and unavailable evidence separate.
- Saved overlay/artifact endpoints bind the event to the requested image and apply case-level access control. Current API proof verifies anonymous401 and wrongimage/run404. Artifact availability is explicit, not an instruction to locally derive a missing panel.
- `POST /api/cases/{case_id}/stenosis-measurements` requires a scoped case clinician reviewer, savedimage/run/candidate identity, finite comparable diameters, explicittrue calibration/reference attestations, evidence text and protocol identity. It creates an append-only measurement snapshot; it does not mutate predictions or independently certify supplied measurements.
- Human assessment is persisted independently of model scores. Reviews must bind the image and analysis event. No expert approval is invented for these research cases.
- Research reports snapshot saved analysis, human review and provenance. Export permission is separate; do not invoke an unguarded real-image report path that derives boundaries during local saved-output proof.
- Existing async job creation is documented for the product architecture, not permission to execute it locally on medical images or launch training under the current freeze. Saved-output proof disables inference and geometry generation.

Actual receipt: `reports/execution_readiness_20261030/same_case_geometry_run365636956/PERSISTENCE_API_RECEIPT_20261105.json`. Full source route inventory: `reports/milestone3/SOURCE_API_INVENTORY.json`. No API tokens or passwords are included.
