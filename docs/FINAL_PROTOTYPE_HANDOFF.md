# CoroVision research prototype handoff

Run `python3 scripts/run_local.py` from this checkout and open [CoroVision](http://127.0.0.1:8000/). The server binds to loopback and serves the production frontend with the API. Run `python3 scripts/check_local.py` in a second terminal to check the default installation. See [fresh-clone setup](FRESH_CLONE_SETUP.md) for another machine and [local demo](LOCAL_DEMO_RUN.md) for account setup. Use the existing pinned model archive for inference.

## Demonstration

1. Sign in and open Research Cases. Show that case access is scoped to the account. Demonstrate upload, preprocessing and preview with a synthetic or approved image.
2. Open a saved 2D result in Analysis & Explainability. Show the artery mask, centerline and model provenance. Refresh the exact saved URL and download the artery mask.
3. Switch to Localization. Select a saved stenosis candidate and show its location and raw detector score. In Severity Review, explain that the reviewed diameter reduction calculation takes compatible explicit inputs. Synthetic bands A and B are used in software tests. The app keeps severity unavailable where a configured, reviewed protocol is absent.
4. Open Reports & Exports. Show run identity on the 2D report and its exports. For a completed 3D segmentation, export the research JSON, stage CSV and PDF. The 3D PDF identifies the case, run, model and snapshot and shows the unavailable downstream stages.

## Acceptance receipts

- Build and frontend tests from `frontend`: `node --test tests/*.test.mjs && npm run build`. All 20 tests passed. The production build reported a large chunk warning.
- Backend: `.venv/bin/python -m pytest -q` from the backend directory passed 231 tests. Five opt-in real-artifact tests were skipped.
- Browser: headless Chrome via Playwright verified the rebuilt app on port 8000. It automatically restored run `9568e91f-8f0d-4661-8f2c-41d2b30f0031` on `public-arcade.png` after refresh. The saved candidate overlay was visible. The downloaded artery mask matched the browser artifact before and after refresh (SHA-256 `10049a8829b2c7fd0cf3147494289201512d399080a4b87e2de34d7814d03510`). A separate viewer session could not open the case. This run has no saved ordered width profile.
- The authenticated PDF endpoint exported the existing completed volume run `d0fbbf42-e090-4fb5-a586-65eaab605321` with its run ID in the attachment filename. The generated PDF in this check had SHA-256 `d86769ab79c5ff27b4ab29fc4816404d0434ea81f652c52c29e9e5c2b126a804`.
- The default health check confirmed that the frontend and API responded and the installed inference models were available. This check did not launch inference.
- Local demo roster access requires an explicit local opt-in, a loopback host and peer, and a nonproduction environment.

## Research acceptance still open

The documented comparisons support using the retained 2D segmentation and stenosis baselines. Clinical diameter and severity need calibrated expert references. Independent localization and unseen-patient performance need an eligible cohort and checkpoint exposure evidence. Actual model attribution and faithfulness require a verified diagnostic run. The 3D segmentation workflow reports 3D stenosis, vessel measurements and severity as unavailable where the saved run lacks supporting outputs. The current handoff is local. Target deployment, container startup and capacity still need receipts. See the [prototype acceptance rules](../reports/research_progress/PROTOTYPE_ACCEPTANCE_20261109.md) and [saved research status](MILESTONE2_3_STATUS_20261106.md).

## Follow-up verification

The saved DCA1 width-profile graph and JSON download were verified before and after refresh. The scoped SQLite and storage recovery drill also served the same width evidence and a saved CTA PDF from a separately started restored copy. See the [closeout evidence](../reports/milestone_closeout_20261109/README.md) for scope and remaining gates.
