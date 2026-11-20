# Backend/API test results — 16 November 2026

Command: from `backend/`, `./.venv/bin/python -m pytest tests -q`.

Result: **321 passed, 5 skipped, 51 warnings in 70.25 seconds**. Skips are opt-in/external-model checks and are not counted as passes. Warnings are Starlette/httpx and scikit-image/NumPy deprecations. Covered APIs include authentication, cases, uploads, preprocessing, saved analyses, frozen-model contracts, 2D/3D geometry, measurements, severity authorization, reports, artifacts and cross-user isolation.

An initial invocation from repository root produced 55 collection errors (`ModuleNotFoundError: app`); this was an invalid working directory and is retained here for command reproducibility.
