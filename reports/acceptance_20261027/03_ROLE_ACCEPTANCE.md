# Phase 3 — Role-based acceptance

Evidence: full backend JUnit and 14 frontend checks. Relevant suites:
test_rbac_system, test_auth_module, test_auth_extended, test_role_workspace_policy,
test_shared_workflow, test_admin_clinical, test_operational_policy,
test_review_reporting and test_research_progress.

| Role | Automated coverage |
| --- | --- |
| Doctor / Clinician | Separate roles and review labels; explicit case access; run-linked human assessments; no automatic AI grading |
| Medical Researcher | Authorized case/upload/analysis flow; scoped history and artifact/report ownership; no cross-user substitution |
| Data Scientist / ML Engineer | Evaluation/research workspace role gating; navigation does not confer case operations; job controls not falsely connected |
| Administrator | Administrative and clinical-section access where granted; operational grants cannot self-approve or bypass resources; promotion/history gates |
| Viewer / Technician | Explicitly limited navigation and actions; analysis needs separate grants; denial of research/admin-only evidence |

Reports remain bound to saved case/image/run, with unauthorized/foreign resources
denied. Session revocation/account disablement and role changes are covered by
automated assertions. These are fixture acceptance tests, not human usability,
institutional identity-provider, multi-institution or clinical-signoff proofs.
Browser proof from earlier task-checklist work is available separately; this
audit did not manually log into each role or complete every role's visual flow.
