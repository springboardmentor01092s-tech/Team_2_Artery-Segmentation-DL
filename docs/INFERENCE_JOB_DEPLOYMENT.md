# Persistent research inference jobs

Install the application-specific mask archive and dependencies using TRAINED_RELEASE_INTEGRATION.md. Keep private environment configuration, storage and database outside source transfer. Configure a strong private JWT secret; do not copy test credentials into deployment.

Run from the application root in a compatible Python environment:

```powershell
python -m pip install -r backend/requirements.txt -r backend/requirements-ai.txt
$env:COROVISION_INFERENCE_WORKER = '1'
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1
```

In a separate terminal:

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

These loopback addresses are for the laptop running the application. This does not expose the training laptop to the other laptop or configure a production reverse proxy/TLS deployment.

## Persistence and execution

Startup creates the additive `analysis_jobs` table through existing SQLAlchemy initialization. Back up an existing database before deployment. No checkpoint or historical result is migrated to new weights. Existing events without versioned explanation data remain readable and are not retroactively invented. Latest-result backfill checks the original overlay/event association and does not attach current validation to unidentified old weights.

- POST `/api/images/{image_id}/analysis/jobs` with a caller-generated `idempotency_key` returns HTTP 202 and the persistent ID. Backend determines models, input and user; no client result/model path is accepted.
- GET `/api/analysis/jobs/{id}` returns pending, processing, completed or failed with timestamps, coarse progress (0/10/100), result reference or sanitized error. Progress is a state indicator, not an ETA or epoch percentage.
- GET `/api/analysis/jobs/{id}/result` returns its immutable saved event only after completion. GET `/api/images/{image_id}/analysis/jobs` lists recent jobs for refresh/recovery. All require existing case access.
- A unique active-image slot prevents concurrent jobs for one image. The same caller/image/idempotency key returns its existing job; a new intentional rerun gets a new event. The UI preserves the key after a transport failure and resumes job polling on revisiting an image.
- One in-process worker dispatches inference sequentially. The existing model mutex and exact model adapters remain. The queue admission limit is 32 pending/processing jobs; stale pending jobs expire after 30 minutes.
- Processing interrupted by a restart is recorded as failed with `worker_interrupted`; it is not automatically rerun. Pending jobs remain queued and are rechecked for current account/grants/case access, input hash and model version before execution. Review a failed job and request a new explicit run if appropriate.
- Saved masks and float score arrays use authenticated event-specific artifact endpoints. PNG masks are discrete 0/255 in the prepared frame; NPZ contains float artery and returned-mask stenosis scores, loaded with `allow_pickle=False`. The latter does not recover suppressed/missed detections or represent patient disease probability. Original-image candidate bounds use the stored ROI/padding transform with clipping warnings; no native-resolution segmentation claim is made.

## Operational limits

Exactly one API process is supported. Do not deploy `--workers 2`, multiple replicas or overlapping reload processes with this worker enabled: restart recovery is not a multi-host lease protocol. `COROVISION_INFERENCE_WORKER=0` disables automatic dispatch for tests/maintenance; do not leave it disabled while expecting the queue to run. There is no separate autonomous GPU/training dispatcher.

An in-process inference call has no hard kill timeout. Queue expiry is not an execution deadline; a stuck inference requires operator restart and explicit review of the interrupted job. Multi-host leases, process isolation/hard timeout, crash-orphan storage cleanup, managed object storage and production operational monitoring remain separate work. The request itself returns promptly and the browser can revisit saved status rather than holding a synchronous inference request open. The old synchronous analyze endpoint is retained for compatibility and rejects requests when an image job is active; new UI uses jobs.

Keep original filenames and supplied metadata de-identified, review DICOM content/burned-in text, and follow the data owner's retention policy. Basic decoder/tag checks are not comprehensive medical-data governance. This research build has two pre-existing permission-policy test failures; their exact intended policy must be resolved separately before operational acceptance.

## Verification

```powershell
$env:PYTHONPATH = 'backend'
python -m pytest backend/tests/test_integration_pipeline.py backend/tests/test_trained_release.py -q --tb=short
# Enable installed-checkpoint/background-worker test only where the pinned archive is installed:
$env:CV_TEST_REAL_TRAINED_RELEASE = '1'
python -m pytest backend/tests/test_trained_release.py -q --tb=short
```

The automated fixtures are synthetic and temporary. Use the manual acceptance checklist in INTEGRATION_PLAN.md for a permitted representative image and the other laptop. Browser visual review and target-laptop installation must not be inferred from API tests/build success.
