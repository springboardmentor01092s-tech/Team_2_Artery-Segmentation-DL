# Fresh-copy verification — 23 October 2026

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
