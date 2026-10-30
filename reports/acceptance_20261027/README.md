# CoroVision six-phase acceptance audit — 27 October 2026

Scope: existing baseline application, synthetic/de-identified fixtures and saved
Kaggle evidence. No new training, pooling, production promotion or deployment.

| Phase | Evidence report | Current acceptance |
| --- | --- | --- |
| 1 | [Integration](01_INTEGRATION.md) | Software integration checked; five real-checkpoint opt-ins skipped |
| 2 | [Model/data QA](02_MODEL_DATA_QA.md) | Existing provenance/limitations reconciled; no independent-validation claim |
| 3 | [Role acceptance](03_ROLE_ACCEPTANCE.md) | Automated role/RBAC regressions pass; human/browser sign-off outstanding |
| 4 | [Security/privacy](04_SECURITY_PRIVACY.md) | Functional safeguards checked; synthetic backup/restore implemented and tested; not a penetration certification |
| 5 | [Performance/capacity](05_PERFORMANCE_CAPACITY.md) | Liveness HTTP microbenchmark only; inference/GPU/peak-memory/capacity unverified |
| 6 | [Packaging](06_PACKAGING.md) | Exact macOS dependency constraints and Node lock available; Docker build blocked by missing runtime |

Full backend command from `backend`:
`.venv/bin/python -m pytest tests -q --junitxml=/tmp/corovision-acceptance-20261027.xml`

Result: **139 passed, 5 skipped, 118 warnings in 66.51 seconds**. Machine record:
`backend-junit.xml`. New backup tests added after this run: **4 passed in 0.15s**.
Frontend: `node --test frontend/tests/*.test.mjs`: **14 passed**.
`scripts/check_local.py`: API healthy, frontend available, inference models ready.
Readiness proves configured availability, not correct trained predictions.

The original full run used a short test-only JWT secret. Its fixture was lengthened
afterward to remove avoidable warnings; production configuration was not changed.
Starlette/httpx and Pillow deprecations remain maintenance items. The Vite build
previously warned about a large JS chunk; no bundle-performance claim is made.

Do not label all six phases fully accepted. Missing native inference, independent
generalization, clinical measurement/severity validation, production load/security
review and container/clean-machine recovery remain explicit release gates.

## Final regression after remediation

Full backend re-run including backup tests: **143 passed, 5 skipped, 3 warnings
in 68.18 seconds**. Record: `backend-final-junit.xml`. Test-only short-JWT warnings
are resolved; Starlette/httpx and Pillow deprecations remain. `pip check` reports
no broken requirements. Frontend build passed in 2.07 seconds, with the existing
large-chunk warning. `git diff --check` passed. Limited source-pattern scan found
no matching OpenAI/Google key literals in inspected app/frontend/scripts/docs;
this is not a full credential/history or vulnerability audit.

Saved report routes verified available through the existing allowlisted evidence
API. No active analysis jobs were present before the local application restart.
