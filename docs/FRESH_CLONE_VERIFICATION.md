# Fresh-copy verification

Verified using a clean temporary copy of the application branch on macOS Apple Silicon with Python 3.13. No existing application database, uploaded images, model weights, private environment file, or installed project dependencies were copied into it.

| Check | Outcome |
| --- | --- |
| Backend dependency installation | Passed in a newly created virtual environment |
| Frontend locked dependency installation (`npm ci`) | Passed |
| TypeScript and Vite production build | Passed; bundle-size advisory remains |
| Local demo-account generation | Passed; credentials remained private and ignored |
| Backend tests | 59 existing application tests passed; new portable-setup test also passed |
| Frontend tests | All 6 passed |
| Single-server application startup | Passed on localhost:8000 |
| API health, frontend HTML, referenced assets and original logo | Passed using `scripts/check_local.py` |
| Repeated setup preserves private configuration | Passed in the portable-setup regression test |
| Model availability without weights | Correctly reported unavailable; no training launched |

The backend tests cover authentication, case isolation, uploads/preprocessing, review/report workflows, and role policies. Two old tests were updated to match the previously requested Administrator doctor capabilities without removing case-scope checks. An orphaned training-only test was removed because its training module is deliberately absent from the published application branch.

Non-blocking test warnings remain for the HTTP test client and a short **test-only** signing key; setup generates a separate long random key for the local runtime. Optional GPU inference and external SSO/email providers were not verified. Windows and Linux launch paths are implemented but have not been exercised on physical Windows/Linux laptops.

This is software portability verification, not clinical validation or a guarantee across every OS, GPU, Python version, or DICOM transfer syntax.

## Local Docker first-install follow-up — 20 November 2026

The production Compose profile was additionally exercised with a disposable
empty database and Chromium. The owner created the first administrator through
the interactive `docker compose exec app python -m app.cli create-admin`
workflow. The second bootstrap was rejected. The administrator then completed
TOTP enrolment, created a one-time email-bound invitation, and a Viewer
redeemed that invitation in the browser. The database and administrator session
survived a container restart. The probe also confirmed that login credentials
were not persisted in browser local storage.

`python scripts/preflight.py` currently checks Docker, Compose, private `.env`,
the Compose/Dockerfiles and 4 GiB free disk. It passed on the test host on 20
November 2026. Details are retained in
[`reports/RELEASE_TESTING_20261120.md`](../reports/RELEASE_TESTING_20261120.md).

This is not a clean GitHub-clone acceptance of the current uncommitted working
tree and is not hosted acceptance. A clean clone from a reviewed published
revision, HTTPS, external-secret handling, and an authorized target remain
required before claiming deployment readiness.
