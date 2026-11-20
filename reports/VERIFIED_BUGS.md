# Verified bugs and discrepancies

| ID | Severity / category | Evidence | Expected versus observed | Fix and regression |
|---|---|---|---|---|
| QA-01 | Medium / confirmed source behavior | `backend/app/main.py:1207–1218` | A rejected upload should preserve valid prior case evidence. The rejection helper commits failed workflow/processing status without checking prior valid state. Current audit was source-only. | Preserve last valid state separately from failed intake; add disposable valid-case plus rejected-upload regression |
| QA-02 | Low / documentation discrepancy | `git ls-files research_training`, seven entries | Application publishing policy describes excluding training runners; tracked source still contains them | Clarify scope and reconcile only with branch-owner authorization |
| QA-03 | Low / environment gap | `backend/tests/test_legacy_detector_normalization.py:3–5`; AI requirements | Torch-dependent collection requires the AI profile. AI suite collected; base-only failure remains unverified. | Document profiles or conditionally skip AI-only collection; verify both clean environments |
