# Confirmed defects and repairs — 16 November 2026

## Open

- **UI-NAV-01 · MEDIUM · M2/M3:** In the live authenticated browser, `Analysis history` and `Open analysis` did not replace the case overview for either preserved case. React click handlers exist in `frontend/src/App.tsx`; root cause and repair are not yet established. No speculative code change was made. Add a state-transition/component regression before repair, then repeat 2D/3D browser flows.
- **TEST-CMD-01 · LOW:** `npm test` is not defined although Node tests exist. The valid command is `node --test tests/*.test.mjs`. Consider adding a package script.

## Reconciled, not defects

- Preserved real 2D `Unavailable/Indeterminate` results are justified `low_local_boundary_contrast` abstentions, not a disconnected service.
- 3D perpendicular cross-sections and area-equivalent diameters exist in `volume_measurements.py`; older reports calling them absent are outdated.
