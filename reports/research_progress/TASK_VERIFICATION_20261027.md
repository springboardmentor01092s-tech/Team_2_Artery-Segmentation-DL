# Task software verification — 27 October 2026

Command, from backend directory:
`.venv/bin/python -m pytest tests/test_research_progress.py tests/test_vessel_centerline.py tests/test_review_reporting.py -q`

Result: **16 passed, 7 warnings in 5.70 seconds**.
Warnings concern Starlette/httpx deprecation and the isolated test-only JWT key
length, not a disclosed production secret. An initial invocation from the app
root failed import collection; corrected backend-directory command passed.

Frontend: `npm run build` passed (2.03 seconds); Vite warns about a large JS chunk.

## What these tests prove

- Evidence API requires authentication and research/admin/ML-engineer access;
  missing, corrupt, stale and outside-root evidence is handled conservatively.
- Task-proof statuses cannot claim completion; software/research status lacking
  an available allowlisted evidence file falls back to verification required.
- Synthetic Y-shaped mask produces three paths, one grouped junction and three
  endpoints; cycles are retained; empty/disconnected/uncertain masks are flagged.
  A centerline map is saved in the fixture. This is algorithm behavior, not
  patient-level anatomical correctness or clinical diameter validation.
- Saved research reports bind the case/image/analysis/model and reviewer;
  seven-panel manifest and actual fixture overlay are accessible only to owners.
  Missing landmarks remain unavailable. JSON/CSV/PDF export works; history is
  immutable across subsequent runs; absent measurements remain unavailable.
- Frontend TypeScript compiles and production build completes. Browser visual
  verification is separate from the build check.

## Not proven

No trained checkpoint executed in these tests (isolated legacy/fixture provider).
No new training, pooling, frozen ensemble or unseen-data evaluation occurred.
No clinical severity, patient independence, model calibration, full security
audit, production load test, Docker build or deployment is established.
Original baselines and protected data were not modified.

## Follow-up verification

After adding malformed-proof handling, research-progress suite re-run:
**8 passed, 5 warnings in 3.81 seconds**. Null task lists and non-string proof IDs
fail closed. Browser signed in as Demo ML Engineer shows 20 task groups; expanding
the vessel task displays the software proof and remaining patient-validation gap.
Screenshot: `task-checklist.png`. The application was restarted using the existing
database and accounts. No Kaggle training/evaluation job was launched this turn.
