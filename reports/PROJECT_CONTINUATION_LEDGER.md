# Continuous execution ledger - 11 November 2026

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
