## 20 November 2026 — Administrator MFA and invitations

- Production administrators now enroll a time-based authenticator during password sign-in. Protected routes require a factor-verified session. Codes are single-use per counter and use the existing login throttle. The server-owner recovery command resets enrollment and revokes sessions. Existing development demo roles retain their demo sign-in.
- Administrator User Management issues email-bound, single-use invitations valid for 24 hours. Production signup requires an invitation and creates a Viewer account. Existing UI role assignment and case grants apply after signup. Production OAuth account creation is disabled. Browser login tokens and demo sessions use tab storage and clear legacy persistent credential entries.
- 16 backend tests passed for first-admin bootstrap and concurrent creation, recovery, authentication and enrollment, replay denial, invitation permission and redemption. Production frontend build and diff checks passed.
- Fresh container and Chromium probe passed. Interactive CLI bootstrap prompted for credentials, declined repeat bootstrap, and the browser enrolled the first administrator, opened User Management, created and redeemed an invitation, and reopened the administrator session after restart. Awaits readiness before bootstrapping, following the documented startup order. The disposable runtime was built from the verified Debian candidate with updated backend code and frontend assets. This checks empty installation state and browser behavior. A fresh remote GitHub clone, hosted TLS, and a published release build remain unverified. Authenticator secrets are stored in the application database. Replay is documented in `reports/admin_access_20261120/`.
- No scientific acceptance changed. No hosted deployment was performed. Next, run the updated release from a clean source checkout and reconcile the remaining image findings before hosted acceptance.

## 20 November 2026 — Debian candidate, PostgreSQL report recovery and closeout audit

- M4-04 advanced. Built `corovision:trixie-local-acceptance` from the current application with the isolated Dockerfile under `reports/base_refresh_20261120/`. Index SHA-256 is `959d30df05d68560fc7a4ee4b45b46d44791bb55f292453b430efa3f58a2255f`. The offline scan found 0 critical and 123 high package findings, compared with 3 critical and 68 high in the original baseline. This trade-off leaves image selection and security acceptance open. The production Dockerfile was unchanged.
- The network-disabled candidate passed `pip check` and the two-job capped probe. The single worker completed both synthetic jobs at 182.7 and 377.4 seconds. Each generated one exact-run report, owner PDF/CSV/JSON all passed, unrelated researcher requests returned 404, and no OOM kill was recorded. The disposable container was stopped and removed.
- Disposable PostgreSQL 16 passed HTTP-path report persistence, all four export formats, authorization and immutable history using the deterministic reporting fixture. Dump and restore reproduced all saved report rows byte for byte. Snapshot SHA-256 is `a2cfb90cd711a148b3ea16a74abc368a936928e0118109942f7dd393f5571e0a`. The initial sandboxed initdb was blocked by shared-memory restrictions. A socket-only isolated rehearsal passed on retry and was stopped. Replay from `backend/` with `sh ../reports/base_refresh_20261120/postgres-report-probe.sh`.
- Regression: `.venv/bin/python -m pytest -q` from backend returned 331 passed and five skipped. `node --test tests/*.test.mjs` from frontend returned 20 passed. The acceptance matrix records local software checks independently of scientific and hosted acceptance.
- Recorded ImageCAS-X v3 publisher metadata and reconfirmed ASOCA's permission gate. Dataset licensing, patient exposure and native-grid pairing remain unresolved. Two local sweep notebooks contained zero executed cells and zero outputs, and One Touch was absent. No threshold was selected. Calibrated reference validation and matched-target XAI randomization remain open. No training, protected testing or deployment occurred.
- Next local security action: check the scan-indicated zlib1g fix against the candidate's package sources and re-scan an isolated patched candidate. Review the remaining high package findings before release selection. Logs, scan and replay materials are under `reports/base_refresh_20261120/`.

## 20 November 2026 — Mandatory correctness policy

- Added `COROVISION_CORRECTNESS_POLICY.md` and linked it from both workspace instructions. Updated the existing active backlog review to read the policy on every run. The schedule and execution restrictions were preserved.
- Software verification: 30 focused backend tests passed across report authorization, saved measurements, 3D cross-sections, XAI checks and integration. One dependency deprecation warning was emitted. These checks establish software behavior within the test scope.
- Scientific validity: independent segmentation and calibrated stenosis reference gates remain open. Prior model faithfulness results and the unresolved randomization control remain unchanged. No training, protected evaluation or deployment was performed. The next engineering task remains M4-04 base-image remediation and candidate runtime verification.

## 20 November 2026 — Concurrent queue capacity and Python refresh

- Two simultaneous synthetic submissions passed on the existing production image in a disposable network-disabled container (2 CPUs, 4 GiB, 256 processes, OMP/MKL threads set to two). The single worker completed jobs sequentially at 183.0 and 379.7 seconds from polling start. Each produced exactly one report tied to its own completed run. Owner PDF, CSV and JSON succeeded for both and separate researcher requests returned 404. The runtime reported no OOM kill. A processing sample recorded 1.981 GiB and 17 processes. This establishes the tested local two-job scope.
- A separate derivative image updated pip to 26.3 and setuptools to 84.2.1. Dependency consistency, network-disabled imports and production readiness passed. Offline Trivy reduced Python high findings from eight to one, a setuptools declaration in pip's vendor metadata. Debian remained at 60 high and three critical. The derivative has not undergone the concurrent workload. No checked-in deployment files changed.
- Probe, logs, Dockerfile and offline scan are under `reports/concurrent_capacity_20261120/`. M4-04 stays IN_PROGRESS. Next, evaluate a refreshed Debian base and run the capped workload on the selected candidate. Hosted verification still requires an authorized target. The One Touch volume was absent and no new scientific references or training readiness evidence were verified.

## 20 November 2026 — Final deck media and rehearsal verification

- Verified the finalized [PowerPoint](../final_artifacts/CoroVision_AI_Milestone_4_Final_20261120.pptx) with the exact saved XA prepared frame, XA overlay and CTA slice embedded. The original candidate required an image-embedding repair discovered during render review. All seven slide renders were inspected. Slide 6 labels the ML Engineer evidence-library screenshot separately from the researcher automatic report. The finalizer passed package, layout and Artifact Tool import checks. Final verified SHA-256 is `b6f2287b66681fbb882d1de20539ff7019872a1f7068a0bb993403c7baf98482`.
- Rehearsed the researcher path from overview through Reports & Exports to saved v3. The exact report ID, evidence gallery and PDF, CSV and JSON controls reappeared. The populated ML Engineer comparison walkthrough and role-navigation evidence are recorded below.
- M4-03 stays PASS for the local handoff. The next local engineering task is M4-04 concurrent capacity and dependency remediation. No application source or checkpoints changed for this presentation check.

## 20 November 2026 — Final presentation and handoff

- Finalized `final_artifacts/CoroVision_AI_Milestone_4_Final_Reviewed_20261120.pptx`. The seven slides cover traceable intake, saved 2D and 3D evidence, task-specific metrics, automatic reports and roles, and the separate clinical/deployment blockers. Rendered all seven slides and inspected each at full size; no clipping, overlap or unreadable text was observed.
- Presentation finalization passed package integrity, exact 7-slide count, 16:9 geometry, heading fit, Arial font policy and Artifact Tool re-import. PPTX SHA-256: `a347efc6f662c690b4602e25dbeb8bb29e0c901529319970a666e9fb2c48c68e`.
- M4-03 is PASS for local presentation and browser scope. The historical comparison remains aggregate-only and does not establish per-case scientific superiority.
- Final Trivy JSON evidence contains 3 critical and 68 high findings; Pillow is absent. M4-04 remains in progress for remediation/risk acceptance and representative concurrent capacity.
- `/Volumes/One Touch` was absent again at handoff. The prior mounted interval exposed historical reservation material but did not establish a current shared owner, live quota or immutable input revision. R-01 remains blocked. M2-01 and M3-01 remain blocked on eligible independent cohorts and qualified expert references. M3-02 remains incomplete because a checkpoint-specific randomized matched target is unavailable.
- No deployment, commit or push occurred. Next executable engineering task: refresh the Python dependencies/base image, rebuild and rescan, then run representative concurrent capacity. Scientific tasks require the named external inputs.

## 20 November 2026 — Populated browser architecture comparison

- Local ML Engineer browser path passed: Model Evaluation → Model evaluation → Analytics views → Comparison. The existing historical validation report rendered two ARCADE artery architecture rows with 200 validation images each. Dice rendered as 0.7432 and 0.7257. The IoU control changed the chart to 0.5913 and 0.5695.
- Fixed missing provenance on the analytics card by rendering the comparison report's optional limitations field in `frontend/src/ModelAnalytics.tsx` and typing it in `frontend/src/ModelWorkspace.tsx`. `npm --prefix frontend run build` and `git diff --check` passed. Browser reload verified the per-case identity limitation alongside both rows. This passes the populated browser display and metric switching with the existing historical report. Matched per-case scientific comparison remains unverified.
- M4-03 remains in progress for presentation review and rehearsal. The seven-slide candidate and rendered slides are under `.codex-build/presentation/`. The One Touch volume remains unavailable for readiness reconciliation. No checkpoint, clinical validation, deployment or publication activity occurred.

## 20 November 2026 — Capped production-image report probe and offline scan

- M4-07 PASS for local engineering. Ran the existing image `corovision:automatic-report-acceptance` at `sha256:48e8039d4b43c04ad25a4026a402768361eacbbff84b2f71fa54a81f47693eeb` with network disabled, two CPUs, 4 GiB memory, 256 processes and OMP/MKL thread limits of two. The first startup correctly rejected a missing signing secret. A retry used a generated, disposable signing secret. The actual worker completed the synthetic queued job in 166.8 seconds, beyond the prior native test's 150-second polling window. Exactly one report matched the completed run. PDF, CSV and JSON returned to the owner and all returned 404 to a separate researcher. The probe validated the PDF header. One usage sample showed 1.955 GiB and 14 processes. The test container was stopped and the logs retained.
- M4-04 remains IN_PROGRESS. Trivy 0.76.2 scanned the same image offline using the cached advisory database dated 19 November, with DB updates, version checks and telemetry disabled. It reported 68 high and 3 critical package findings. Debian accounted for 60 high and all three critical findings, with no fixed Debian version listed for any of those entries in this scan. Python accounted for eight high findings, including vendored package metadata. No high or critical Pillow finding appeared. Review affected paths and test a refreshed base and updated Python dependencies in an isolated build. General concurrent capacity and authorized hosted acceptance remain open.
- Evidence and replay probe are in `reports/capped_report_20261120/`. No application source changed. The next independent acceptance work is populated model comparison in the browser and presentation verification. Independent reference and model-readiness gates remain open. One Touch was absent.

## 20 November 2026 — Automatic report browser acceptance

- PASS for local report discovery and reopen. In the researcher browser session, Reports & Exports listed automatic report v3 for the XA DICOM case. Selecting it displayed report `20c7617f-577b-4160-a609-84da8db34d42`, run `dc9ca584-4dbe-49d7-b250-2f81e40bd010`, the evidence gallery, and PDF, CSV and JSON controls. A read-only SQLite query linked the report to completed job `530bdf04-32ca-4de1-a779-53016219ed8d`. No new download was exercised in this check.
- Next local check: capped-image acceptance with persistent diagnostics. The One Touch volume was absent during this check. No application files were changed.

# Continuous execution ledger - 11 November 2026

## Frozen automatic-report API acceptance

The extended opt-in real-checkpoint test completed successfully in 100.51 seconds. The actual background dispatcher completed a frozen queued run, generated exactly one report bound to its result event, and returned a valid PDF to the owner while denying the unrelated account. Reproduce from `backend/` with `CV_TEST_REAL_TRAINED_RELEASE=1 .venv/bin/python -m pytest -q tests/test_trained_release.py::test_real_case_upload_analysis_and_access_control`. The test ran natively against the application API. Browser and container acceptance remain separate.

## Real worker timing diagnostic

The thread-capped retry also reached the previous 40-second worker deadline with the job still processing. Extended only the opt-in test's polling window to 150 seconds and launched the real-checkpoint test again (terminal session 58088). It must still reach completed state and pass the automatic PDF and access checks. No production timeout changed.

## Real-checkpoint automatic-report verification attempt

Docker Desktop was manually paused. Used the installed local frozen models as an independent verification path. Extended `test_real_case_upload_analysis_and_access_control` to require the queued run's automatic PDF and outsider denial. The opt-in test completed direct analysis but failed its existing 40-second worker deadline with the job still processing, before reaching the new report assertions. Keep M4-07 open. Distinguish a worker that completes after the deadline from an inference failure by running the next attempt with persistent job state and captured timing.

## Automatic report release acceptance follow-up

Image `corovision:automatic-report-acceptance` built successfully (index `sha256:48e8039d4b43c04ad25a4026a402768361eacbbff84b2f71fa54a81f47693eeb`). A network-disabled capped disposable instance accepted the synthetic queued upload but did not produce a verifiable completed report within the polling window. End-to-end frozen container/browser acceptance remains open. Added fault-injection coverage demonstrating that a report exception preserves completed analysis and logs the report failure. The complete integration-pipeline suite with Pillow 13 passed 10/10. At inspection, One Touch was not mounted, so the shared threshold-sweep reservation and validation input remained unverifiable.

## Automatic-report image build

Started `docker build -t corovision:automatic-report-acceptance .` in the dedicated checkout (terminal session 68001). This includes the latest queued-report worker. The full backend regression with isolated Pillow 13 passed 330 tests with five skips. When the new image is available, verify automatic report creation through a queued HTTP job in isolated storage and reopen it in Reports & Exports.

## Replacement image verification

The Pillow 13 rebuild completed as `corovision:pillow13-recheck`, image index `sha256:e23af845dbbfdbc1275defea3fbd288dd1fa688b275770963b52f50579131713`. A network-disabled container verified Pillow 13.0.0, dependency consistency and the retained 2D checkpoint hashes. The rebuild predates the automatic report worker change. The permission reviewer blocked Docker Scout rescan because it may export image contents or derived data. Use an approved locally executed scanner with an advisory database and no image upload. The previous vulnerability findings remain the published evidence for the previous image only.

## Automatic reports for completed 2D jobs

The queued 2D worker now saves an immutable research report against its completed run when the requesting user has export permission. The existing Reports & Exports workflow serves PDF, CSV, JSON and Evidence ZIP. A report-generation failure is logged separately so the completed analysis remains available. Integration tests verified one report per completed job, correct run binding, owner exports and outsider denial. The focused backend suite passed 19 tests, three frontend evaluation tests passed, and the production frontend build passed. Dashboard and compatibility-gated comparison use the existing routes and views. Populated browser comparison remains unverified.

## Pillow remediation and rebuild

Updated the application requirement to Pillow 13.x to address scan findings on runtime 11.3.0. Tested with an isolated Pillow 13.0.0 install. All 17 focused preprocessing, saved-measurement and reporting tests passed. Started the replacement image build as `corovision:pillow13-recheck`. Image completion and rescan remain pending.

## Production image vulnerability scan

Docker Scout finished indexing image `ca1a2a788127` (linux/arm64, 306 packages). The final summary reported 216 findings across 37 packages, including 6 critical and 66 high severity. The runtime confirmed Pillow 11.3.0, which Scout flagged. Scan execution passed, but security acceptance remains open. Review the dependency bounds and base image, rebuild, rerun image-handling regressions, and rescan before hosted acceptance.

## Seeded XAI randomization target correction

The diagnostic previously reused the original candidate's rank after randomization, which could compare a different detection. Updated the script to seed a disposable copy and find an eligible same-class spatial match before deriving its attribution. Eight XAI tests passed, including the retained-score filter regression. Ran the corrected diagnostic on C3 of saved run `4157543d-5df7-482d-ba49-f354619a3b43`. Deletion advantage 0.222643 and insertion advantage 0.129512 passed. The randomized model had zero matched score and no eligible target, so the attribution comparison was unavailable. Faithfulness remains unestablished. No retained weights changed.

## Remaining acceptance reconciliation

Container `python -m pip check` reported no broken requirements. Docker Scout still had no vulnerability results after indexing began. The checked local artifacts and mounted execution-readiness directory had no validation threshold sweep JSON or completion receipt. The exploratory 2D benchmark, role navigation and comparison API evidence remain valid. Independent reference scoring, populated browser comparison, final presentation and threshold selection remain open.

## Capped 3D workload check

Ran offline frozen 3D inference on a synthetic 64³ anisotropic NIfTI in the built image with 2 CPUs, 4 GiB and a 256-process limit. The checkpoint hash and source mask dimensions matched. Runtime was 6.77 seconds and cgroup peak memory was 937,254,912 bytes. This passes a single synthetic workload under the caps. Docker Scout 1.28.0 started scanning the local image and reached indexing.

## Compose resource caps

Added adjustable Compose defaults of two CPUs, 4 GiB memory and 256 processes. An isolated loopback Compose instance reached healthy status. Docker inspection confirmed all three caps, then the instance was stopped. This validates capped startup. Workload capacity and image vulnerability scanning remain open.

## Container 3D upload-to-worker acceptance

Started a separate loopback Uvicorn service inside the built container using a temporary database and storage, the hash-pinned 3D checkpoint, and CPU execution. The authenticated synthetic anisotropic NIfTI upload returned HTTP 202. The worker completed run `4318b108-9950-430b-b8f8-cadd5097e90a`, and the saved result matched the checkpoint digest. The Evidence ZIP run ID and all member SHA-256 hashes matched. The temporary service stopped after verification. Docker inspection confirmed the existing Compose container has no explicit CPU, memory, or process caps. Image scanning, resource limit configuration and hosted verification are open.

## Container 3D authenticated exports

Executed the frozen model against a synthetic anisotropic NIfTI in the isolated container, then registered the completed synthetic fixture as run `8b838238-aa8a-410b-a46d-729d1e32e78f`. The running service returned 200 for the case owner, 404 for an unrelated researcher and 401 for anonymous requests for JSON, CSV, PDF and ZIP. ZIP case/run identities and all member hashes matched. This verifies the saved 3D export routes. The service upload and worker path with a configured 3D checkpoint, scanning, and resource checks remain open.

## Container 3D inference smoke test

Ran the retained 3D checkpoint on a synthetic anisotropic NIfTI in the built local production container. The separate bind-mounted invocation did not produce a result, and Docker copy was rejected by the read-only root. Streamed the existing checkpoint into the writable temporary mount and selected it for the smoke-test process only. Frozen CPU inference passed: expected checkpoint hash, source mask dimensions and affine, and three output previews verified. The long-running service configuration was unchanged. This verifies in-container inference. Authenticated 3D HTTP exports, scanning, and resource-limit acceptance remain open.

## Container authenticated report and restart acceptance

The synthetic HTTP analysis exceeded the client's 90-second timeout, then persisted run `c23171b3-4c9c-43b5-b52a-408b86d31beb`. Reused that result without rerunning inference. Isolated report `f1712489-c11a-4c60-86de-a77fdf0fab85` returned HTTP 200 for the owner, 404 for an unrelated researcher and 401 for anonymous requests across PDF, JSON, CSV and Evidence ZIP. ZIP artifact hashes matched. After restarting the container, the same report's stored run binding and authorized PDF download passed. This verifies 2D report persistence on the container's named volume. Container 3D checkpoint, scan and resource checks remain open.

## Local production container acceptance increment

Docker production build completed as `corovision:local-acceptance` (image index `sha256:ca1a2a788127514c59b64e104db9c64d5ad119e10f9f0c51aaf6e34586774a0e`). Started the existing Compose service in project `corovision-local-acceptance`, bound to loopback port 18000 with separate named storage and an ephemeral secret. Compose health passed. After restart, readiness reported database, storage, frontend and worker ready. The 2D release passed its hash checks and ran synthetic CPU inference. The frontend returned HTTP 200 and anonymous 2D/3D PDF routes returned HTTP 401. The read-only root and named data volume were verified. Optional 3D checkpoint was unavailable inside the image. Authenticated export, persisted-record restart, scanning and resource-limit checks remain open. The isolated service is running for follow-up. No hosted changes.

## Local production container build

Started Docker Desktop. `docker build --check .` completed without warnings. Started `docker build -t corovision:local-acceptance .` from the dedicated checkout. The frontend build and runtime dependency installation completed, then the build reached the configured GitHub model archive download/install step. Image export and container startup were not yet observed. M4-04 is in progress. The eight focused XAI faithfulness/integrity software tests passed. Existing checkpoint faithfulness conclusions remain partial. No hosted deployment or new training run occurred.

## Milestone 2 alternate evaluation execution

DCA1 exploratory inference completed on 129 strictly binary image/mask pairs with the hash-verified retained 2D artery model. Mean image Dice 0.571798 and IoU 0.415585. Five ambiguous masks were excluded. Reconciled the recovered 700/150/150 ImageCAS split manifest hash with the retained epoch-75 attention-trial binding. ImageCAS-X case intersection, original exposure clearance and native-grid pairs remain open. See `MILESTONE_2_INDEPENDENT_EVALUATION.md`.

## DCA1 mask preflight

Read-only Pillow inspection found a matching ground-truth PGM for all 134 publisher-bound DCA1 images, with matching dimensions for every pair. Five masks contain more than two intensity levels. Verify their label encoding against the publisher documentation before scoring or freezing a binarization rule. Patient independence and checkpoint exposure are still unverified. No benchmark scores were produced.

## Milestone 2 ASOCA access verification

Official UK Data Service study 855916 lists both ASOCA volume/mask archives as closed access and requires depositor permission. The searched local inventories contained the catalogue HTML but no matching archives. Added an access-request draft and scoring acceptance steps in `MILESTONE_2_INDEPENDENT_EVALUATION.md`. M2-01 remains blocked on approved paired 3D data, checkpoint exposure clearance and an eligible 2D reference cohort.

## Milestones 1 and 2 verification follow-up

M1-01 remains passed for the selected `173d0ff` baseline. Verified that the retained pre-upgrade dump opens with PostgreSQL 16 `pg_restore -l` and lists case and user data without the later research reports table. The earlier completed rehearsal supplies the restore and idempotence evidence.

M2-01 remains blocked for independent scoring. The existing exposure audit identifies ARCADE as development data, leaves checkpoint exposure unresolved for CARDIAG and CADICA, and identifies ImageCAS-X as unsuitable for independent scoring until ImageCAS lineage is reconciled. [ASOCA](https://asoca.grand-challenge.org/Home/) is a concrete 3D candidate, with 40 CCTA scans and expert consensus voxel annotations described in the [dataset paper](https://www.nature.com/articles/s41597-023-02016-2). These sources establish annotation scope. The next step is to obtain access to the paired volumes and masks, reconcile patient/source overlap with the retained checkpoint manifests, and verify native-grid alignment before freezing the scoring cohort. No new independent metrics were generated.

## M1-01 historical PostgreSQL upgrade and rollback

Selected the repository schema at `173d0ff` as the supported rehearsal baseline because it includes persistent inference history and predates run-linked clinical review and research reports. Generated the legacy schema from that revision's SQLAlchemy models on an isolated PostgreSQL 16 Unix socket and seeded a synthetic owner and CTA case. Extended `backend/app/migrations.py` to apply the existing additive upgrades using PostgreSQL-compatible column types and defaults.

Before upgrade, captured a custom-format `pg_dump`. Ran the startup schema sequence and repeated the upgrader. Verified every current ORM table column and read the preserved case and owner. Restored the pre-upgrade dump into a separate database. It retained the case and owner and lacked the new review column and report table. The temporary cluster stopped. Focused SQLite case/history and report tests passed 12/12. Existing working database was outside the rehearsal. PostgreSQL HTTP/report acceptance remains open. Next independent item is M4-03.

## Populated comparison API acceptance

Extended the isolated dashboard/model registry fixture to require authenticated `GET /api/analysis/status` to return the complete configured comparison report. `.venv/bin/python -m pytest -q tests/test_dashboard_model_registry.py` from `backend/` passed both tests. The comparison fixture is synthetic and temporary. The populated browser chart and final presentation remain open under M4-03.

## Comparison data source clarification

The analytics architecture chart reads `status.comparison.experiments` from the legacy model status payload. The backend resolves that report from `models/segmentation/comparison_report.json`. The Experiment Lab import is a separate workflow. For M4-03, verify populated comparison with an isolated, compatible fixture for the actual surface being tested. Importing a record into the Experiment Lab alone does not establish that the legacy chart is populated.

## Final presentation content brief

Mapped the final presentation to seven evidence-backed slides in `reports/MILESTONE_4_PRESENTATION_BRIEF.md`. The brief links to the accepted local exports, role walkthrough, development model evidence and outstanding acceptance conditions. A rendered and reviewed deck remains pending under M4-03.

## Milestone 4 clinician walkthrough

Demo Clinician opened the assigned severity queue and used Enter to open the XA DICOM evidence. The Clinician's Decision form, saved outputs, and separate automatic measurement assessment were visible. No assessment was submitted. This completes the scoped primary-navigation check across all seven demo roles. M4-03 remains in progress for populated compatible comparison and final presentation.

## Milestone 4 technician walkthrough

Demo Technician selected the assigned saved XA DICOM case and opened Data & Uploads. Confirmed the upload picker, preprocessing profile selector, and quality check with saved preprocessing record v2.2. This verifies intake navigation for the technician role. No files were submitted. M4-03 still needs the clinician path, compatible populated comparison, and final presentation.

## Milestone 4 administrator walkthrough

Demo Administrator opened User Management, Roles & Permissions, Workspace & Case Access and Audit Logs on the loopback demo. Confirmed account/access-request panels, the operational permission matrix, separate case authorization and recorded administrative activity. This passes read-only navigation for these four views. No accounts, grants or case records were changed. M4-03 still needs the remaining role paths, populated comparison and final presentation.

## Model comparison fixture review

Reviewed `reports/segmentation_comparison_20261029/REPORT.md` for a populated comparison fixture. The two historical architecture pairs have reported split-level aggregates but missing independently reproduced per-case identity. The verified 200-case postprocessing comparison uses one frozen checkpoint with two processing configurations. Preserve these distinctions in the handoff. The historical reports can illustrate metric interpretation, while a populated controlled architecture browser comparison still needs compatible records with explicit evaluation bindings.

## ML engineer comparison walkthrough

Demo ML Engineer opened Model Evaluation and its Comparison tab. The browser exposed same-task and metric controls and showed that no comparable metrics had been imported for the selected view. ARCADE validation and binary-mask metric scope were identified separately. No experiment was imported or activated. This verifies the empty-state behavior. A populated comparison with compatible records, remaining role checks and final presentation are still open under M4-03.

## Milestone 4 doctor walkthrough

Demo Doctor opened the assigned Severity Review queue and activated the XA case's evidence and assessment action with Enter. The browser showed the saved evidence, measurements, exploratory assessment and a separate Doctor's Decision form. The pointer click timed out in browser automation, while keyboard activation succeeded. No assessment was submitted. M4-03 now has researcher, assigned viewer and doctor navigation evidence. Final presentation and remaining role checks stay open.

## Milestone 4 viewer walkthrough

In the isolated local browser, Demo Viewer opened Assigned Cases and selected PUBLIC-CTA-CHECK-1f26ed. The read-only view showed pending review, no recorded review and no approved report. Researcher upload, model evaluation and research export controls were absent. This verifies the assigned viewer path. Remaining M4-03 checks include the reviewer walkthrough and final presentation.

## Frozen checkpoint preflight

Read-only SHA-256 verification of the retained One Touch Kaggle v2 `maskrcnn_resnet50_fpn/best.pt` matched the planned digest `f0bc898c95b6efdd53863d5a430fb4b850c2451b440c5a53b92a73e73c5be2e3`. This verifies the local checkpoint copy. R-01 still requires live quota, ownership and provider source binding. M4-03 remains the next independent engineering item.

## M4-06 saved 3D browser export acceptance

Chrome downloaded JSON, CSV and Evidence ZIP individually from public CTA run `75c30403-db57-42ee-b513-fecf4490a868`. Reconciled these with the earlier browser PDF whose four pages passed visual review. The ZIP manifest matched the exact run and all 10 member hashes. JSON values, CSV bytes and per-page PDF text matched the standalone downloads. M4-06 passes for this local saved run. Next independent task is M4-03 role-specific walkthrough and final presentation.

## CTA machine-readable browser export attempt

On saved run `75c30403`, clicked the JSON, CSV and Evidence ZIP controls in the in-app browser. The run stayed selected and no export error appeared. No new matching files appeared in Downloads. Browser file delivery remains unverified. The PDF visual pass and handler-level checks remain valid. Next check is to export individually in Chrome and identify each file by content.

## Saved CTA PDF visual acceptance

Rendered the browser-downloaded PDF for run `75c30403-db57-42ee-b513-fecf4490a868` with Poppler and visually inspected all four pages. Text, identity table, geometry, candidate abstention, limitations and page numbering were readable, with no visible clipping or overlap. PDF visual acceptance passed. Browser JSON, CSV and Evidence ZIP verification remain open.

## Saved CTA browser PDF receipt

Recovered the previous in-app browser download under its actual generic filename, `research-report (1).pdf`. Its creation timestamp matches the export attempt. PDF parsing confirmed four pages and exact run ID `75c30403-db57-42ee-b513-fecf4490a868`. The browser PDF download therefore passed. Visual inspection and browser downloads of JSON, CSV and ZIP remain open.

## Saved CTA browser reopen

Demo Researcher reopened PUBLIC-CTA-CHECK-1f26ed, selected completed run `75c30403-db57-42ee-b513-fecf4490a868` from the saved run selector, and observed 25 paths and 251.04 mm traced. All four export controls were present. The in-app browser did not return a download event for the PDF click, and no matching file appeared in Downloads. Browser export and visual PDF acceptance remain open. Retry from Chrome and verify the actual downloaded files.

## 3D export authorization regression

Extended `backend/tests/test_volume_inference.py::test_volume_job_case_permissions_history_and_artifact_isolation` to exercise JSON, CSV, PDF and Evidence ZIP. Each returned 401 for anonymous requests, 404 for an unrelated researcher and 200 for the case owner. The focused test passed. M4-06 still requires browser downloads and visual PDF inspection. One Touch is mounted again. Live quota and shared ownership still need reconciliation for R-01.

## Milestone 4 demo walkthrough

Added the saved 2D and 3D report sequence, export reconciliation checklist and role/model comparison rehearsal to `docs/LOCAL_DEMO_RUN.md`. The walkthrough is ready for rehearsal. M4-03 remains open for the role-specific browser walkthrough and final presentation. M4-06 still needs browser downloads and visual PDF inspection. The One Touch volume remained unavailable.

## 18 November 2026 shared execution storage check

At 15:23 IST, `/Volumes/One Touch` was absent. The local historical reservation and sweep clearance files remain readable, but they cannot establish current shared-lock ownership or provider quota. R-01 remains blocked until the shared volume is accessible and live provider state can be reconciled. The local application was still listening on port 8000, so M4-06 can proceed independently.

## Saved 3D export reconciliation

Called the application export handlers as Demo Researcher for retained public NIfTI run `75c30403-db57-42ee-b513-fecf4490a868` using a read-only database session. All 10 ZIP member checksums matched the manifest, manifest case/run identities matched the saved run, ZIP JSON matched standalone JSON, CSV bytes matched, and extracted text matched across all four PDF pages. Handler reconciliation passed. Browser downloads and PDF visual checks for this run remain open.

## PostgreSQL upgrade scope check

Confirmed PostgreSQL 16 tooling is installed and the existing migration entry point exits for PostgreSQL. The documented fresh-schema restore already passed. Legacy upgrade acceptance requires an identified older PostgreSQL schema for the supported upgrade path. M1-01 now records that dependency explicitly. Next independent work is M4-03, starting with the role-specific browser walkthrough and the saved 3D export evidence.

## Training authorization update

The owner explicitly authorized resuming CoroVision training in this chat. Before dispatch, reconcile the live provider's available compute and active jobs with the shared execution lock, verify the exact checkpoint and eligible train/validation dataset, and select a finite experiment with documented acceptance criteria. Start with the unresolved frozen-checkpoint threshold sweep. Its latest recorded attempt has no usable output. Reserve the protected test split for evaluation after selection. No new run was dispatched during this authorization update.

## 18 November 2026 consolidated acceptance and liveness evidence

Added `MILESTONE_4_FINAL_ACCEPTANCE.md` to map original PRD requirements to verified evidence and gaps. Local liveness benchmark returned 60/60 HTTP 200 at concurrency 1, 4 and 8. Docker daemon still unavailable. Next engineering checks remain isolated PostgreSQL legacy upgrade and run-bound 3D browser export reconciliation.

## 18 November 2026 report gallery and handoff verification

M4-01 passed in Chrome as Demo Researcher. Opened XA DICOM v2, run `d74e1154-9492-4f3c-8b29-5e326ce9e8b1`, and PNG v1, run `ae72625c-1949-4dd0-b9c0-6c663325facd`. Each gallery rendered a decoded 512-pixel-wide original and centerline image. Neither displayed the unavailable landmark card. Existing snapshots were used.

M4-03 inventory identified `docs/LOCAL_DEMO_RUN.md`, `docs/DEMONSTRATION_EVIDENCE.md` and `reports/public_case_demo_20261109/README.md` as existing demo material. The only discovered PowerPoint in the workspace was a Milestone 3 build candidate. Final Milestone 4 presentation acceptance and the role-specific browser walkthrough remain open. From `backend/`, `.venv/bin/python -m pytest -q tests/test_dashboard_model_registry.py tests/test_role_workspace_policy.py tests/test_evaluation_workspace.py tests/test_review_reporting.py` passed all 12 tests.

Docker still fails to connect to the daemon socket. PostgreSQL legacy upgrades remain open because `backend/app/migrations.py::upgrade_local_schema` returns for PostgreSQL. The next implementation task is to establish the supported legacy schema for M1-01 and exercise a migration using a disposable database. Final project acceptance remains partial.

## Cross-session handoff

Added continuation rules to the workspace and dedicated checkout `AGENTS.md` files and seeded `reports/MASTER_PROJECT_TASK_QUEUE.md`. Next executable task is M4-01. From the dedicated checkout, run `python3 scripts/run_local.py` if the local app is stopped, then open the saved XA DICOM v2 and raster reports. The frontend build and diff check passed for the landmark change. Browser acceptance after that change remains pending. Existing checkout changes were preserved. This handoff setup adds no training, deployment, commit or push authorization.

## 18 November 2026 PDF and terminal validation closeout

The retained XA DICOM report path now converts the selected DICOM frame to an in-memory PNG for ReportLab while preserving the original upload unchanged. Regression coverage verifies a printable PNG source and unchanged saved overlay. Browser-created immutable report v2 `449db7f6-014e-4659-b1e2-680c37cc35e1`, bound to run `d74e1154-9492-4f3c-8b29-5e326ce9e8b1`, downloaded successfully. Poppler rendered all five A4 pages; visual inspection confirmed both the original angiogram and saved overlay on page 2 and no clipping, overlap or broken glyphs. Historical v1 remains unchanged as evidence of the discovered defect.

Final application verification: **330 backend passed, 5 opt-in external/model checks skipped; 20 frontend passed; production build PASS; `git diff --check` PASS**.

Kaggle validation version 2 reached a terminal platform state with zero active events, but version history records **Ran in 0 seconds** and the immutable notebook contains no execution count or outputs. It is therefore a no-op, not a successful threshold sweep or training run. No threshold was selected, no protected test split was loaded, no checkpoint was promoted, and no new scientific result is claimed. A further remote dispatch was not made. Independent clinical/reference validation, XAI faithfulness completion, production deployment and operational acceptance remain external blockers; they cannot be manufactured by application tests.

## 17 November 2026 input-browser and saved-measurement closeout

Fresh browser engineering acceptance now covers all intended input paths. JPEG case `FRESH-JPEG-20261117-1638` saved and reopened run `8a6e72c1-944e-457d-8383-5108bd10b8f5`. Eligible XA DICOM case `FRESH-XA-DICOM-20261117-1639` validated source spacing `0.2,0.2`, saved and reopened run `d74e1154-9492-4f3c-8b29-5e326ce9e8b1`. Direct multi-file intake reconstructed 16 de-identified synthetic classic-CT slices and completed run `8e6025c1-ab36-40df-8e31-34f6fcd127b8`; that fixture establishes transport/software behavior only. The public NIfTI run is `75c30403-db57-42ee-b513-fecf4490a868`.

Two saved-report defects found during acceptance were repaired. Short 3D paths with no eligible bilateral reference window no longer call `min()` on an empty sequence; the public NIfTI report now completes with 25 extracted paths, zero candidates and 251.04 mm traced. Retained XA DICOM sources are decoded through the DICOM source loader rather than Pillow. Browser reassessment of the exact saved XA run now associates path P3 and safely abstains for insufficient boundary contrast instead of reporting a decoder error. Focused measurement/report regression: **20 passed**. Final verification: **329 backend passed, 5 opt-in external/model checks skipped; 20 frontend passed; production build PASS; `git diff --check` PASS**. No training, deployment, commit or push occurred. The application engineering input matrix is closed; overall scientific/clinical/production acceptance remains PARTIAL.

## Volume upload progress and runtime recovery

Added actual XMLHttpRequest upload progress for NIfTI/ZIP/direct DICOM volume submissions, accessible progress/status text and a distinct post-upload geometry-validation state. Network/timeout errors advise checking saved history before retrying to avoid duplicate submissions. Production frontend build PASS.

Attempted saved CTA browser navigation from the pre-build open tab: console reported a failed dynamic import for an old `CaseWorkflow` asset. Reload then returned connection refused. Restarted current built application with `./backend/.venv/bin/python scripts/run_local.py --port 8000`; Uvicorn startup completed and bound localhost successfully. This interrupted attempt is not a browser acceptance pass. Pending journey requires a fresh page load against the restarted server.

Fresh follow-up browser acceptance PASS for the NIfTI volume path. Against the restarted current build, the public de-identified `CTACardio_original_hu.nii.gz` fixture reached a visible 100% upload indicator and the distinct `Upload complete. Validating source geometry…` state. New run `75c30403` completed in 7.77 s for `512 × 512 × 321` source voxels with 342 predicted coarse-grid voxels and rendered all three orthogonal previews. A full page reload reopened the same completed run and values. No training, checkpoint change or clinical/scientific claim was made. The saved measurement panel remained on its loading placeholder and is excluded from this pass; JPEG, eligible XA DICOM and direct DICOM-series browser journeys remain open.

## Populated PostgreSQL recovery continuation

Added guarded reusable `scripts/rehearse_postgres_records.py`. On localhost port 55439 seeded synthetic user/case/volume analysis into `corovision_rehearsal_source`, dumped and restored to fresh `corovision_rehearsal_restored`, and verified case ownership, run linkage, source identity and abstention. Source/restored canonical snapshot SHA-256 both `3352aaf7252e54c74a1f76982452e932fcb40c8592f0a08d4395cd2f187b2375`. Server stopped afterward. ORM persistence and populated recovery PASS; HTTP/report workflow, legacy schema upgrade and full deployment acceptance remain incomplete. No training dispatch, public deployment, commit or push occurred.

## DICOM geometry and PostgreSQL rehearsal increment

Added classic CT SOP-class, per-slice dimension/spacing consistency, finite orientation/origin and orthonormal-axis checks. Added malformed geometry and mixed-study assertions to the preserved synthetic series test. Affected tests: **14 passed**, one dependency warning. `git diff --check` passed.

Disposable PostgreSQL schema creation (31 application tables), custom-format backup, restoration into a distinct database and restored table-count verification passed. Server stopped after testing. See DEPLOYMENT_READINESS_NOT_DEPLOYED.md for exact scope and temporary artifact path. Populated API/report workflows and legacy upgrade migration remain NOT_TESTED. No public deployment or training dispatch occurred.

## Autonomous continuation — sweep draft repair

Research suite executed with the installed application ML environment: `./.git-publish/backend/.venv/bin/python -m pytest research_optimization/tests -q`: **150 passed**. System Python failed collection because torch is absent; that attempt is not counted as passing. New package binding regression: **1 passed**. Repaired notebook SHA-256 `e6f58453788b392e8398cc2e86403b85dfb89aa2d7d932867384c38e53042735`; runner hash unchanged.

Live Kaggle private draft: imported repaired notebook; selected explicit ARCADE source version 2 instead of latest, Internet off, draft session off, T4x2 and displayed quota `00:00 / 30 hrs`. The checkpoint-input menu does not expose version pinning, so immutable checkpoint-output revision reconciliation remains pending in addition to shared-lock closure. No Save-and-Run submission or optimizer update occurred. Preserve the current private draft for continuation. Full milestone acceptance remains PARTIAL; this entry does not close browser input, XAI, reporting or operations acceptance.

## Restored drive / live Kaggle reconciliation — 17 November 2026

One Touch is mounted again. Live Chrome inspection of authorized account `mokshagnamannam` showed **0 Active Events**. The shared execution lock still describes the November 12 reservation and is stale; its old quota fields are not dispatch clearance.

Live stenosis sweep run **369018210**, version 1, failed after **14.8 seconds**, GPU T4 x2, zero output bytes. Logs identify an assertion on missing hard-coded train/validation annotation paths under `/kaggle/input/annotated-x-ray-angiography-dataset/data`. This is not a completed threshold evaluation. Source packager now discovers a unique train/validation root using the unchanged expected annotation hashes; it rejects zero/ambiguous bindings. A separate repaired notebook is prepared under `artifacts/stenosis_sweep_repair_20261117/` in the local research workspace, preserving historical payloads. No retry or training dispatch occurred; immutable input-version and fresh compute/sole-owner gates still require verification.

## Conditional training authorization and direct-intake regression

Full backend command `cd backend && ./.venv/bin/python -m pytest tests -q`: **327 passed, 5 skipped, 51 dependency deprecation warnings in 74.25 seconds**. The five opt-in checks remain skipped. Frontend `node --test tests/*.test.mjs`: **20 passed**. No failed executed tests.

The owner explicitly authorized resuming training **after dataset, compute and experiment gates pass** in this chat on 17 November 2026. This supersedes the earlier pause only when those gates are satisfied. No optimizer update or remote dispatch occurred. `/Volumes` currently contains Macintosh HD and Recovery only; the One Touch drive holding shared datasets and the execution lock is not mounted. Training dispatch is BLOCKED pending restoration and fresh reconciliation of eligibility, shared lock, provider status/quota and a finite reviewed experiment. Historical authorization/quota fields in QUEUE.json are not live provider evidence.

Local queue audit: 2D attention run 368489597 completed 20 epochs and was rejected; baseline retained. 3D attention run 368667223 failed exact baseline-count parity before optimizer updates (delta TP +1, FP -2, FN -1); no accepted improvement is recorded. Existing gates were preserved.

Added `backend/tests/test_direct_dicom_intake.py`: anonymous/viewer/outsider rejection, one-slice/empty-slice rejection and exact multipart-to-archive handoff all PASS. This uses a stub and establishes transport/security behavior only, not neural inference or real-series acceptance. Frontend regression: 20 passed. Full backend regression was launched separately. Local browser reload confirmed the application remains accessible; no new input acceptance is claimed.

## Consolidated remaining-work execution — direct DICOM implementation

At base revision `f2ea58743af251706bc4d509e140321cf024bb18`, added a researcher/admin direct multi-file CT upload endpoint and connected the 3D form to it. The endpoint bounds slice count, per-file bytes and aggregate bytes and reuses the existing authorized ZIP reconstruction/inference pipeline. Client selection shows file count and aggregate size; full percentage progress and pre-inference metadata preview remain pending. Single-file NIfTI is no longer required when slices are selected.

Reconstruction now checks all submitted files for CT modality, identifying metadata, consistent study/series, and missing/duplicate SOP identity before GDCM selection. Mixed or unreadable entries cannot silently disappear from the reader's selected series. The privacy fixture was isolated from unrelated ZIP/NIfTI outputs to preserve its intended assertion under stricter directory validation.

Verification: volume preprocessing tests **13 passed** following the change. Earlier combined volume regression was **22 passed, 1 skipped** before the stricter all-file validation. Frontend production build passed for the direct-input implementation; a final rebuild follows the required-field correction. Browser acceptance and dedicated direct-endpoint integration tests remain pending; no full acceptance is claimed.

Docker preflight: `docker info --format '{{.ServerVersion}}'` failed because `/Users/lingareddydhanushkumar/.docker/run/docker.sock` does not exist. Actual Docker image/Compose verification remains BLOCKED_BY_ENVIRONMENT. Training remained paused. No deployment, commit or push occurred.

## 17 November 2026 remaining-input implementation continuation

Base revision: `f2ea58743af251706bc4d509e140321cf024bb18`, with existing evidence changes preserved. Source inspection found the inference API already accepts a ZIP containing exactly one de-identified CT series and reconstructs it before inspecting the volume. `VolumeInference.tsx` incorrectly restricted the picker and client validation to NIfTI. The picker now accepts ZIP and explains the existing reconstruction checks. This is an intermediate implementation, not direct multi-file intake acceptance.

Verification: `cd frontend && npm run build` PASS; `cd backend && ./.venv/bin/python -m pytest tests/test_volume_preprocessing.py -q` **13 passed**, one Starlette dependency deprecation warning; `git diff --check` PASS. No fresh JPEG, XA DICOM, NIfTI or CCTA browser journey was executed in this continuation. Direct multi-file selection, progress, metadata summary and browser acceptance remain incomplete. The searched checkout `external_artifacts` and `storage` contained no `.jpg`, `.jpeg` or `.dcm` fixtures; broader source discovery remains necessary before concluding inputs are unavailable. Existing PNG PASS is preserved. No training, commit, push or deployment occurred.

CAD-RADS-informed update: added `COROVISION_CADRADS_INFORMED_XCA` v1.0.0 using the existing evaluator, authorization registry, saved-run pipeline and export structure. Exact 0/25/50/70/100 continuous boundaries and uncertainty are tested. Original five-category protocol remains unchanged. Chrome verified both selector options and inactive state; no production authorization was recorded. Full backend suite: 293 passed, 5 skipped; frontend production build passed. Focused follow-up tests for exact protocol authorization and sensitivity integration passed 21 tests. See `research_validation_followup/CADRADS_INFORMED_PROTOCOL.md` and `CADRADS_PROTOCOL_BROWSER.jpg`.

Training is frozen. No Kaggle execution, model promotion or checkpoint editing is authorized by this task.

| Task | Implementation | Verification / evidence | Remaining work |
|---|---|---|---|
| Saved-run geometry | Exact run mask/original files loaded, inverse resize mapped, unique path/component screening, branch rejection, candidate-local cross-sections | `test_saved_measurement.py`, `test_stenosis_measurements.py` | Real-image anatomical association and overlap remain topology-screen limitations |
| Sensitivity | One-source-pixel erosion/dilation, nominal image contrast held fixed, range and max deviation recorded | Controlled synthetic narrowing test | Method is sensitivity, not confidence; real-reference validation unavailable |
| Protocol authorization | Role-scoped explicit authorize/deactivate API, actor/time/history, Research Mode only | `test_research_protocol_authorization.py` | Production protocol remains inactive until owner action |
| Frontend | Persisted assessments show widths, narrowing, source coordinates, path, sensitivity and grade state | Production build | Actual saved-case browser verification pending |
| Reports | New snapshots include automatic evidence; CSV preserves records; PDF displays status/widths/range/reasons | Reporting integration tests | Download consistency browser check pending |
| Manual browser import | Backend image/endpoint/hash/schema validation and snapshot lock implemented | Synthetic backend round trip | Chrome file upload blocked by extension file-URL permission |
| Geometry regression | Nine fixtures and original errors preserved | `NINE_PHANTOM_LOCAL_RESULTS.json` | Curvature/noise errors remain; no scientific accuracy claim |
| Real reference collection | 20-frame exploratory pilot prepared | Prior 43-file integrity verification | Zero completed manual MLD/RVD pairs |
| Scientific evaluation / XAI | Existing evidence preserved | Prior exposure / XAI reports | No qualified QCA, no exposure-cleared cohort, detector attribution execution gates unresolved |

Browser blocker observed: fileChooser.setFiles requires Chrome ChatGPT extension `Allow access to file URLs`. No browser permission was changed automatically.

Resolved by owner action: actual synthetic browser CSV export -> backend image/geometry validation -> cohort lock -> reopen passed on 11 November 2026. The 20px/40px values and all identity fields restored after refresh. Browser snapshot receipt SHA-256 matched the downloaded CSV. See `research_validation_followup/REFERENCE_BROWSER_TO_LOCK_VERIFICATION.md`. The old browser-upload blocker no longer applies.

Saved Case 60 processing and refresh were browser-verified. C1/C2/C3 abstained for low local boundary contrast. Browser-created report v3 and downloaded ZIP passed hash and JSON/CSV equality checks. See `research_validation_followup/SAVED_RUN_BROWSER_RECEIPT.json`.

Final full backend regression: **276 passed, 5 skipped, 3 warnings in 72.66 seconds**. Command from backend: `.venv/bin/python -m pytest -q`. Frontend production build passes; `git diff --check` passes. The five opt-in real checkpoint/public fixture checks remain skipped and are not counted as verified external-model behavior.

Both current checkpoint hashes match `ml/releases/corovision_20261023.json`: artery `ea692f8c9c655791a44a340907629cda4e812138a6f15d93cdb2a45166177a7c`, stenosis `f0bc898c95b6efdd53863d5a430fb4b850c2451b440c5a53b92a73e73c5be2e3`.

Live XAI remains held by the documented Kaggle-only execution protocol and unresolved provider/quota/ownership/authorization gates. Real reference agreement remains blocked by zero completed measurements; clinical QCA and exposure-cleared patient cohorts remain unavailable. Protocol activation awaits an actual owner action in the researcher/admin UI; tests did not activate production state.

Resume state: base revision `a8faf5b1f4f6b8ba4c6ba05ff7e91239aeb928c7`, dirty user checkout preserved, no commits or pushes. Backend currently runs on 8000 and frontend on 5173. Next browser test requires extension file-URL permission. Next engineering review should prioritize incomplete candidate coverage, calibration/transform edge cases, and real-reference validation of geometric association. Do not claim those scientific conditions are solved by the unique-path screen.

## 14 November 2026 master-audit continuation

- Current base revision: `b6a7ac097f583f6e4d298293aa6b3484662880ce`; the pre-existing dirty checkout was preserved. No commit or push was made.
- Frontend production build passed. Frontend Node tests: **20 passed**.
- Changed measurement/reporting backend tests: **8 passed** with one dependency deprecation warning.
- Connected Chrome verified the overview, saved 2D case/run `4157543d-5df7-482d-ba49-f354619a3b43`, saved 3D case/run `d2c06ad4-e352-446e-be9a-d0d03544253c`, and report-builder inventory.
- 2D evidence preserved case/image/run identity, source-pixel units when calibration was absent, three candidate-specific MLD/RVD results, distinct raw detector scores, experimental research severity labels, unavailable sensitivity, and no automatic normal inference.
- 3D evidence rendered synchronized saved slice previews, source-grid geometry, a perpendicular-section candidate, distinct diameter and area narrowing, explicit coarse-mask limitations, experimental severity, and unquantified uncertainty.
- Fixed issue `UI-3D-001`: the 3D stage reason was rendered twice above the stage definition list. Removed the redundant paragraph from `frontend/src/VolumeInference.tsx`; the canonical reason remains in the per-stage list.
- Report versions are present (v1-v7). The browser accessibility bridge reports closed native-select options as disabled and could not select one. Source inspection shows the options are not disabled; browser download/reopen verification therefore remains pending rather than failed.
- Full backend regression: **298 passed, 5 skipped, 3 warnings in 71.04 seconds** with `.venv/bin/python -m pytest -q`. Skips remain opt-in external/model checks; warnings are dependency deprecations.
- Training remains paused. No model weights, datasets, credentials, database, uploads, or generated build artifacts were published.

Next exact actions: rebuild after `UI-3D-001`; verify the corrected 3D panel; test report reopen/download consistency; run 1280px and smaller responsive checks; then complete the remaining administration/security and per-control browser inventory. Scientific blockers remain independent patient evaluation, qualified reference measurements, severity agreement, current target-specific XAI faithfulness, and unseen-patient performance.

## 16 November 2026 current audit continuation

Training and checkpoint changes remain frozen.

1. Reproduce UI-NAV-01 with a focused component/browser test; trace `activeView`/`caseSection` state and repair without changing saved evidence.
2. Repeat browser 2D and 3D open-analysis, refresh/reopen and export-download value reconciliation after the navigation repair.
3. Add 3D local proximal/distal same-path reference suitability and perturbation sensitivity; withhold severity when a boundary is crossed.
4. Verify direct eligible DICOM-series intake to inference in an isolated fresh case.
5. Execute checkpoint-specific attribution faithfulness and randomization controls when eligible non-clinical inputs are available.
6. Scientific work requires external evidence: exposure-cleared cohorts, qualified MLD/RVD, calibrated acquisition scale, matched severity grades and native-resolution CTA lumen references.

Reproducible commands:

```text
cd backend && ./.venv/bin/python -m pytest tests -q
cd frontend && node --test tests/*.test.mjs
cd frontend && npm run build
./backend/.venv/bin/python scripts/run_local.py --port 8000
```

## 17 November 2026 final-acceptance closeout

- Registered checkpoints were reconciled: ResNet34 U-Net SHA-256 `ea692f8c9c655791a44a340907629cda4e812138a6f15d93cdb2a45166177a7c`; Mask R-CNN SHA-256 `f0bc898c95b6efdd53863d5a430fb4b850c2451b440c5a53b92a73e73c5be2e3`. Rejected attention work was not promoted.
- Candidate-bound detector Grad-CAM was integrated at revision `82b9a79`. Checkpoint-specific verification passed stability and deletion but failed insertion; randomization had no eligible retained target. Faithfulness remains unestablished.
- Full backend regression: **322 passed, 5 skipped**. Frontend tests: **20 passed**. Frontend production build: **PASS**.
- Fresh browser upload and download/reopen acceptance was not completed because connected browser control became unavailable. Historical browser evidence remains preserved, but the fresh gate is `NOT_TESTED`.
- 3D synthetic geometry remains software-verified. Percentile reference selection, uncertainty, taper-aware bilateral reference suitability and independent CTA comparison remain incomplete.
- Training remains paused. No checkpoints were modified. Deployment remains postponed and was not attempted.
- Authoritative closeout documents are `APPLICATION_FINAL_ENGINEERING_AUDIT.md`, `INPUT_FORMAT_BROWSER_VERIFICATION.md`, `THREE_D_MEASUREMENT_VALIDATION.md`, `XAI_FAITHFULNESS_VERIFICATION.md`, `REPORT_DOWNLOAD_CONSISTENCY.md`, `FULL_APPLICATION_REGRESSION.md`, `DEPLOYMENT_READINESS_NOT_DEPLOYED.md`, `SCIENTIFIC_VALIDATION_LIMITATIONS.md`, and `PROJECT_REQUIREMENTS_ACCEPTANCE_MATRIX.md`.

## 17 November 2026 reliability continuation

- Connected computer control again reported `Local browser access is unavailable for this chat`; Chrome was running. No installed Playwright/Cypress/Selenium fallback exists. Fresh browser priorities remain `NOT_TESTED`.
- 3D geometry method v5 replaced the global path percentile with stable bilateral local same-path references, taper/variation rejection and 0.20/0.25/0.30 mm section-grid sensitivity. Severity is withheld when the range crosses a category boundary. Historical caches remain versioned.
- XAI perturbation now binds scores to the original candidate mask by IoU and uses a per-channel median insertion baseline. Candidate 1 passed deletion only, candidate 2 failed deletion/insertion, and candidate 3 passed both. Randomization remained target-unavailable; faithfulness is still not established.
- Full backend regression: **326 passed, 5 skipped**. Frontend: **20 passed** and production build PASS.
- Deployment preflight and Compose configuration passed; backup/restore, container and operations tests passed 10 tests. Docker image checking was blocked because the Docker Desktop daemon was not running. Nothing was deployed.

## 17 November 2026 fresh browser continuation

- Browser control was restored. A new de-identified PNG case `FRESH-PNG-20261117-112439` completed upload, validation, frozen inference, visualization, automatic measurement assessment, save, full-page reload and exact-run reopen.
- Uploaded source SHA-256: `748a2d4fcd2df8a11e5c1b836abbdf5201d21f75be808e0e71865ef8cda7bf55`. The Evidence ZIP saved original matched exactly.
- Saved analysis: `ae72625c-1949-4dd0-b9c0-6c663325facd`. One candidate was preserved; accepted severity was correctly withheld for insufficient vessel-boundary contrast.
- Immutable report v1: `4db39e95-30fe-4548-b4bf-080a9c4295b0`. JSON, CSV, PDF and Evidence ZIP downloaded. ZIP JSON/CSV matched the standalone downloads byte-for-byte and the manifest identities/hashes reconciled.
- No browser console warnings or errors were recorded on the final report page. Evidence is under `reports/browser_acceptance_20261117/`.
- JPEG, eligible XA DICOM and NIfTI remain `NOT_TESTED`. Direct complete CCTA DICOM-series browser intake is `BLOCKED` because the implemented UI exposes offline/import preparation rather than a direct browser-series workflow. Training remained paused and nothing was deployed or published.

## 20 November 2026 — Local release API, browser, security and performance check

- Corrected invitation redemption ordering so a duplicate-email or duplicate-username request is rejected before it can consume an otherwise valid one-time invitation. Focused administrator/authentication suite: **16 passed**. Full regression already completed in this working state: **333 passed, 5 skipped** backend and **20 passed** frontend.
- The disposable Docker Chromium workflow passed first-admin bootstrap, repeat-bootstrap denial, TOTP enrollment and replay denial, administrator invitation creation, email-bound Viewer redemption, tab-only browser credential storage, and administrator-session persistence through container restart. This is a local Docker scope only, not hosted acceptance.
- Passive HTTP checks passed: `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Referrer-Policy: no-referrer`; anonymous protected routes returned 401 or 403. A bounded health probe completed 20 requests each at 1, 4 and 8 clients with p95 2.140, 2.595 and 7.479 ms. It does not represent inference capacity.
- Lighthouse 12.8.2 finished without runtime error. Accessibility scored 0.96 with zero blocking time and zero layout shift. Performance scored 0.64 with FCP 4.4 s and LCP 11.4 s on the cold local Docker login route. Performance therefore remains **PARTIAL** and requires investigation before a production claim.
- Detailed commands and artifacts are in `reports/RELEASE_TESTING_20261120.md` and `reports/release_testing_20261120/`. No deployment, public scan, training dispatch, checkpoint change, commit or push occurred. The next authorized engineering action is to triage the remaining container findings and cold-login loading path. Hosted acceptance still requires a selected authorized target and a reviewed source revision.
## 20 November 2026 — Clone-ready documentation reconciliation

- Reconciled clone/install documentation with the verified production access policy. The fresh-clone guide no longer instructs users to pass administrator credentials through environment variables or use the legacy wrapper. It now documents the tested interactive `docker compose exec app python -m app.cli create-admin` workflow, first-login MFA, invitation-only production signup, Viewer default role and installation isolation.
- Corrected architecture documentation that still described public Researcher registration. Production registration requires an invitation and creates a Viewer; development registration is distinct. The historical wrapper remains a compatibility shim but is no longer the prescribed setup path.
- `python3 scripts/preflight.py` passed on the test host: Docker 29.9.3, Compose 5.7.0, private configuration, Docker/Compose files and 148.8 GiB free disk. `python -m app.cli --help` exposes only the secure initial-bootstrap and server-owner recovery commands. `git diff --check` passed.
- Active application runtime has no developer-machine absolute path dependency. The remaining `/Volumes` references are documented research/evidence preparation scripts or historical reports, outside the Docker runtime path. A clean clone of a reviewed published revision, hosted HTTPS, secret-management integration and cross-platform acceptance remain open. No deployment, commit, push, training or checkpoint change occurred.
## 20 November 2026 — Clean GitHub release verification

- Cloned the public `lingareddy-dhanush` branch into an empty temporary directory. Revision `f2ea58743af251706bc4d509e140321cf024bb18` was clean. The clone generated a private `.env`, passed preflight and Compose configuration, built the documented image including its hash-validated 2D model release, and reached ready health with persistent storage. The disposable container and volume were removed after the check.
- This is a release blocker: the clean clone's OpenAPI contract lacks `/api/admin/invitations`. Its source does not contain the local MFA/invitation implementation verified earlier in the dirty workspace. No clean-source first-admin/MFA/invitation browser acceptance can be claimed. The required next action is a reviewed source publication, then a repeat of this exact check against its immutable revision.
- Parsed the retained Debian 13 scan: **0 critical, 123 high**. The findings are not security-cleared or risk-accepted. Four Kerberos packages account for 56 findings; core utilities/libraries account for many others. Per-CVE fixed-version, runtime-exposure and mitigation evidence remains required. See `CLEAN_GITHUB_RELEASE_CHECK_20261120.md`. No deployment, training, commit or push occurred.
## 20 November 2026 — Container security inventory

- Added `scripts/export_vulnerability_inventory.py` and generated `reports/base_refresh_20261120/high_critical_inventory.csv` from the retained Debian 13 Trivy JSON. The inventory has **123 high**, zero critical findings. Every row includes CVE, package, installed/fixed version, source URL and explicit blank review fields for runtime exposure, exploitability, remediation and final disposition. All 123 are marked `UNRESOLVED_RELEASE_BLOCKER`; none are silently accepted.
- The exporter completed deterministically and `git diff --check` passed. The next executable security action is package-by-package remediation review against the selected runtime image, followed by rebuild, rescan and regression. No deployment, publication, training or checkpoint change occurred.

## 20 November 2026 — Security remediation priority

- Analyzed the 123-row inventory. Only **two** findings list a fixed version in the retained advisory data: one `setuptools` and one `zlib1g`; **121** list no fixed version. These two are the first concrete remediation candidates. The remaining 121 still require package/runtime-exposure review and are not dismissed merely because a fix is unavailable.

## 20 November 2026 — OAuth credential rotation and current-image security triage

- Recreated the local Docker application after the owner replaced Google OAuth values in the private `.env`. The service reached ready health. The `/api/auth/oauth/google/start` request now emits the registered callback `http://127.0.0.1:8000/api/auth/oauth/google/callback`, includes OAuth state, and reaches Google's identifier page rather than the prior `invalid_client` error. This verifies that Google recognizes the new client; live user consent/callback and CoroVision account linkage still require browser completion.
- Current rebuilt local image `sha256:e0db8cd02d2cf20ed92887f99c8d8678be58e9678a8afef1574a018d373bfe16` has **3 critical / 65 high** offline Trivy findings. Runtime inspection confirms old scanner layers for setuptools/urllib3/msgpack are not the active runtime versions or are absent. The three critical OS libraries are active on app paths for image/DICOM parsing, SQLite persistence, and ZIP handling; their scan records have no listed fixed version. They remain explicit release blockers. Evidence and dispositions: `reports/base_refresh_20261120/CURRENT_REBUILD_SECURITY_TRIAGE.md`.
- Live Google consent reached the application's callback. The provider authenticated the account, but the account already has a CoroVision password identity, so the application correctly declined silent social-account linking. A production configuration defect then sent the safe `existing_account` outcome to the absent Vite port `5173`. `compose.yaml` now explicitly configures `FRONTEND_ORIGIN=http://127.0.0.1:8000`, matching the bundled Docker app and registered callback. Focused auth regression: **6 passed**. The user must sign in normally, then use Profile & security → Connected accounts → Connect Google to link the provider deliberately; a fresh browser link-flow verification remains pending.

## 20 November 2026 — Direct verified Google sign-in for an existing account

- Owner confirmed the existing CoroVision password is unavailable and explicitly requested direct Gmail sign-in. The OAuth callback now links a Google subject only when Google has supplied the exact **verified** email of an existing account, then issues the standard short-lived one-time OAuth ticket and audit event. Unverified provider email remains rejected; a Google subject already linked to another account remains protected by the existing conflict check. New uninvited production accounts remain denied.
- Focused auth regression: **6 passed**. Rebuilt local image and recreated the service; readiness passed and runtime inspection confirms the verified-email matched-account branch plus `FRONTEND_ORIGIN=http://127.0.0.1:8000` are active. Fresh browser Google consent and post-login session verification remain required.
- Performed a clean no-cache rebuild against refreshed public Node/Python bases and current Debian indexes. Offline rescan remained **3 critical / 65 high**; current repositories provide no newer package for the three critical library findings. This is recorded as remediation evidence, not a security clearance. The Dockerfile now places source copying after immutable model installation to avoid future application-source edits forcing a model download.

## 20 November 2026 — Local administrator and final-demonstration access preparation

- Added the existing Google sign-in control to the Create account route as well as the sign-in route. The production-style local configuration explicitly enables verified-Google auto-provisioning only for the least-privileged `viewer` role; invitation and administrator controls remain server-side.
- A verified existing Google account was claimed through the one-time initial-administrator bootstrap flow after confirming no administrator existed. The generated recovery secret was not displayed or recorded. Local database verification confirms exactly one active `admin` account.
- Provisioned six synthetic, active final-demonstration accounts with generated private credentials for the `doctor`, `clinician`, `researcher`, `ml_engineer`, `technician`, and `viewer` roles. Verification found seven active accounts total and exactly these seven distinct roles. No credential values were committed to source or this ledger.
- OAuth ticket exchange now enforces administrator MFA before it issues a browser session. Focused coverage for direct verified-email sign-in, Google viewer auto-provisioning, bootstrap claim of an existing account, and administrator OAuth MFA passed: **14 passed**. The local Docker service was rebuilt, reached ready health, and runtime inspection confirmed these code paths are present.
- This is local engineering preparation only. Fresh interactive browser confirmation of the owner’s Google sign-in and MFA enrollment remains open. The public reviewed source revision still lacks these local changes, so clean-clone release acceptance remains blocked; no commit, push, deployment, training, model change, or credentials publication occurred.

## 20 November 2026 — Isolated final-demonstration role switcher and session floor

- Model Evaluation now provides a dedicated **Training & validation** view using the existing Experiment Lab and its role-based imports and review. The installed-model registry remains in Model evaluation. This UI integration does not supply a validation-sweep receipt or authorize training. The next research action remains the R-01 readiness reconciliation.

### Follow-up: public 2D and 3D Docker upload check

- Authorized cutover completed on port 8000 with the merged volume. Fresh owner-only rollback snapshot at `/private/tmp/corovision-8000-cutover.OXTL86Fj`; original Docker data volume retained intact. Stopped the 8004 writer before attaching the merged volume. Both model families ready, six demo password logins and demo admin MFA challenge passed over HTTP, eight active cases opened under original grants, 17 active reports exported in all three formats, and 18 Trash rows preserved. Credentials file mode 0600. Port 8000 OAuth redirect correct; interactive Google MFA, profile-menu flow and browser Trash UI still pending. Other source service shutdown waits on final interactive verification.

- Rotated only the seven named demo users on the merge rehearsal volume, preserving their IDs and revoking their prior sessions. Credentials generated privately in `/data/demo-credentials.json`; local Compose overlay now sets `DEMO_CREDENTIALS_PATH`. Six roles passed password login and identity verification, ML engineer case-list denial was expected, and the demo admin correctly received an MFA challenge. Across tested non-admin roles, eight cases and 17 reports opened; PDF, JSON and CSV returned HTTP 200 for each report. Created and checked the private 8000 volume-files archive alongside the consistent SQLite backup. Real Google/MFA and remaining case/report access are unverified. The existing unauthenticated token roster is unsuitable for the mixed store. No cutover or service shutdown performed.

- User scoped local consolidation to ports 8001 and 8002 into 8000. Made owner-only SQLite backups and staged case artifacts, then rehearsed ID-aware merge against port 8000's account database. The private volume contains 11 users, 26 cases, 29 images, 38 2D analysis events, 7 volume runs, 24 research reports and 92 case grants. SQLite integrity, foreign keys, image/overlay path existence and seven volume input SHA-256 checks passed. Port 8004 rehearsal is healthy with conventional authentication. A matching clinician password verified 8 visible cases and 17 reports via HTTP. Remaining roles and exports were not verified. Overlapping users retain port 8000 password hashes, so old demo passwords do not necessarily authenticate. No cutover was performed. Source DBs and the original 8000, 8001 and 8002 services remain in place. The merge rehearsal script scopes its inserts to case/workflow tables; source account history and research catalog records require separate reconciliation before full acceptance.

- Single-port consolidation preflight (read-only): standard Docker has 8 users and 0 cases; demo Docker has 7 users, 3 cases, 2 images and 1 volume run; parity has no users or cases. The outer historical DB and restored view each have 9 users, 23 cases and 27 images. A nested historical DB has 8 users, 3 cases and 3 images. Six standard and seven demo emails overlap the outer historical database with different user IDs and matching roles. Forty of 54 historical original/preview references use stale absolute paths, each with one candidate in local storage by filename and parent directory; original source hashes were checked where recorded. The additional local acceptance container on port 18000 has separate storage and was not selected for case import. No databases, volumes or listener state changed. Next rehearse an identity-aware merge on consistent private backups, reconcile all foreign keys and artifact hashes, and verify authorization before cutover. Keep passwordless demo sessions disabled in any consolidated store.

- Fixed QA-01: rejected XCA intake now preserves an established case's workflow and processing statuses while continuing to audit and notify. A disposable SQLite integration test verified first rejection, valid PNG recovery, and subsequent rejection preserving the saved image and both statuses. Focused intake, administrator enrollment and auth suite: 10 passed. Rebuilt parity instance on port 8003; both model families report ready. Offline Trivy still reports 3 critical and 65 high findings. Next: browser onboarding from the isolated standard instance and matched inference evidence.

- Restarted the isolated demo on current image ID `sha256:c01ce5c0d5e322d3cd5ced0636af0a3516bd5194f7c4485f480e0b03b56df8c2`. The same researcher bearer session and CTA run `7c508b17-67e5-40a3-8ee8-3eae88fcd1b0` remained accessible. Standalone JSON and CSV were byte-identical across restart and matched the ZIP contents. All ten ZIP member hashes verified. PDF download passed signature check, but its rendering and byte equality were not asserted. Only the manifest changed among compared non-PDF ZIP members; it includes the regenerated PDF hash.
- Offline Trivy rescan using the existing advisory DB found three critical and 65 high findings on that image. Release security remains open. PostgreSQL and worker crash recovery were not exercised in this restart. Browser onboarding/MFA, same-input native/Docker numerical comparison, eligible positive-candidate Grad-CAM, and historical 2D report reconciliation remain pending. The local backend venv does not have Playwright installed.

- Compared restored development, standard Docker and demo Docker. Standard Docker is source-stale and reports 3D unavailable. Demo checkpoint hashes and inference source match current checkout. Added and config-validated the optional read-only standard 3D overlay. Backend focused regression 31 passed / 1 skipped, frontend 20 passed. See the Docker functional parity matrix, defects and browser acceptance reports. Next prove a fresh isolated standard 3D installation and matched browser workflows. Full parity and scientific acceptance remain open.

- Repeated frozen inference on the same DCA1 image after fixing the early return in the detector explanation path. New run `e6046ea2-9eeb-4fcc-9834-e7b5cc7bda13` saved backbone feature activation and retained zero stenosis candidates. Candidate localization, candidate Grad-CAM and lesion diameter/severity remained unavailable. The focused detector regression passed. The synthetic severity control is display-only and does not produce case evidence. Browser acceptance and an eligible positive-candidate workflow remain open.

- Ran `scripts/verify_docker_public_cases.py` against the isolated demo on port 8001 with `compose.demo.3d.yaml` mounting the retained 3D checkpoint read-only. Both new uploads completed through the normal API.
- DCA1 v1 public angiogram 107, converted from PGM to PNG: `DOCKER-PUBLIC-XCA-c2fffe`, job `246e1ced-41f7-4a3e-8b93-3cd4cb24f89f`. Artery mask, stenosis mask and overlay retrieved.
- Public 3D Slicer CTACardio NIfTI: `DOCKER-PUBLIC-CTA-cdf7ef`, run `7c508b17-67e5-40a3-8ee8-3eae88fcd1b0`. Saved source hash matched the provenance record. Retrieved the native-size mask artifact, coarse probabilities, three overlays and result JSON.
- This verifies Docker upload, worker completion and authenticated artifact retrieval. The Chrome demo was opened, but screenshot and section verification were blocked by Chrome's Apple Events JavaScript setting. Review actions, per-run export retest and full responsive alignment remain pending. Independent accuracy and clinical acceptance statuses remain open.
- Follow-up HTTP acceptance for the same CTA run: the researcher retrieved PDF (28,479 bytes), CSV (1,829), JSON (20,705) and Evidence ZIP (8,018,086). PDF signature, JSON parsing and ZIP member integrity checks passed. All four anonymous requests were denied. Browser download and visual layout for this run, fresh 2D exports and reviewer actions remain open. This check adds no scientific evidence.

- Normal signed-in browser-tab sessions are now configurable through `SESSION_MINUTES`, default to **480 minutes**, and the server clamps all invalid or shorter values to a minimum of **309 minutes**. Tokens remain in `sessionStorage`, so refreshes preserve the login in the same tab while closing that tab/browser does not create an unbounded persistent credential. Focused authentication/operations regression: **20 passed**; frontend production build and Docker configuration validation passed.
- Added `compose.demo.yaml`: a separate Docker Compose project named `corovision-demo`, bound only to `127.0.0.1:8001`, with its own volume/database and explicit development-only local-demo flags. The normal Google-enabled administrator application remains separately healthy on `127.0.0.1:8000`.
- Updated the image seeder to store generated demo credentials only in the isolated writable demo volume, never in the image or repository. The local demo app now has seven synthetic active roles (`admin`, `doctor`, `clinician`, `researcher`, `ml_engineer`, `technician`, `viewer`). Its loopback-only role-switch endpoint returned **7** accounts after startup. The documented `?demo_role=admin` local URL was opened to select the demo administrator and expose the other roles through the app sidebar.
- Docker bridge handling is restricted to the explicit `CV_LOCAL_DEMO_DOCKER_PROXY=1` demo profile, requires a loopback Host origin, and is prohibited by production environment validation. The profile must not be deployed. No credentials/tokens were printed, committed, published, or copied to the normal application database.

## 20 November 2026 — Remaining-work completion (Claude session)

- **Threshold sweep (R-01):** The Kaggle sweep v2 had completed (return code 0, 231.5 s, test not loaded); its full results were only in the notebook log. The 0.25 baseline reproduced exactly. No threshold passed the predeclared gates, so score 0.25 / pixel 0.5 are retained and frozen. Evidence: `reports/stenosis_threshold_sweep_20261120/`.
- **Segmentation boundary metrics:** Added `backend/app/segmentation_metrics.py` (HD, HD95, ASSD, with spacing; 2D and 3D) and connected it to the research training evaluators. Re-scored the retained artery model's frozen predictions on 200 ARCADE validation images: Dice 0.8273 (reproduced), HD95 46.5 px, ASSD 6.05 px. Evidence: `reports/segmentation_boundary_metrics_20261120/`.
- **Grad-CAM++:** Added for the detector (`xai_methods.py`), saved as `.gradcampp.png`, exposed as `gradcam_plus_plus_url` and shown as a viewer layer. Requires a rebuild and a new analysis run.
- **Security:** Added Content-Security-Policy, COOP and HSTS headers (HSTS only behind HTTPS). API docs are hidden when `COROVISION_ENV=production` unless `CV_PUBLIC_API_DOCS=1`. Moved the main `Dockerfile` to Debian 13 (trixie) with `apt-get upgrade`. Draft risk disposition: `reports/base_refresh_20261120/RISK_DISPOSITION_DRAFT.md`. A rebuild and rescan are required.
- **Performance:** API p95 under 8 ms, 32 concurrent requests succeed in 52 ms, page load 0.1 s, 2D analysis about 18 s, 3D about 20 s, report about 0.1 s. Evidence: `reports/performance_20261120/`.
- **UI/UX:** Authenticator screen redesign; local-time fix (UTC timestamps without a zone); layout containment; planned-capability grouping; invite card; review stat cards; audit labels; analysis notice fix. Verified in Chrome on 8000 after rebuild, except for items in the latest uncommitted changes.
- Tests: backend 340 passed (the 5 remaining are environment-only: PyTorch unavailable); frontend build passed, 20/20 tests.
- **Next:** rebuild with the three Compose files; verify headers and Grad-CAM++ on a positive case (ARCADE validation image 18, researcher session); rescan the image; then review and publish to `lingareddy-dhanush`.
