# Frontend and API integration audit — 16 November 2026

Backend: **PASS** for the automated Milestones 1–3 surface (321 passed, 5 skipped). Authorization, cross-case/run isolation, uploads, inference records, candidates, measurements, severity and exports are covered.

Frontend build: **PASS**. Node identity/navigation tests: **20 passed**. There is no `npm test` script; the valid command is `node --test tests/*.test.mjs`.

Live browser: authenticated clinician overview, two case identities, source metadata, processing state and role navigation rendered correctly. **MEDIUM defect UI-NAV-01:** clicking `Analysis history` and `Open analysis` left the visible case panel on `Overview & access` for both preserved cases in the current session. Expected: selected section/workbench becomes visible. React handlers exist in `frontend/src/App.tsx`; reproduction requires `Research Cases` → select either case → click either control. A focused browser regression test and state-transition diagnosis remain required.
