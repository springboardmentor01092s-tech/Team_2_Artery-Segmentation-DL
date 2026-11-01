# Application update - 30 October 2026

This update publishes the application source, software tests and text-based research evidence. It does not include datasets, uploaded medical images, local databases, credentials, model weights or generated builds.

Changes include reviewed stenosis measurements with source/run identity, explicit physical-calibration limitations, Grad-CAM coordinate integrity, volume reporting, offline backup checks and research evidence/comparison views. Historical scores remain historical; advanced prototypes are not presented as newly trained models.

Validation:
- Backend: `.venv/bin/python -m pytest -q` from `backend/`: 162 passed, 5 skipped, 3 deprecation warnings, 68.44 seconds.
- Frontend: `npm run build`: passed; existing bundle-size warning.
- Frontend: `node --test tests/*.test.mjs`: 14 passed.
- Staged whitespace check passed with CSV carriage returns treated as line endings. CSV bytes were preserved to retain recorded artifact hashes.
- Staged source/report scan found no private-key, GitHub-token, AWS-key or Google-access-token patterns. This is a bounded pattern check, not a security certification.

The initial backend command from the repository root failed collection because `app` was not on the import path; the documented backend-directory command above passed. No research trial or model promotion was performed for this GitHub update. Five skipped tests remain unexecuted, not verified.

Local screenshots, image outputs and case receipts remain on the laptop. Reports may refer to those local artifacts; their absence in GitHub must not be interpreted as remote execution proof.
