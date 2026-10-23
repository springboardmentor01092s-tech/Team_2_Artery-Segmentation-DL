# Run CoroVision on another laptop

## Included and excluded

The repository includes application code, required frontend assets, dependency manifests, database models and additive migrations, tests, and setup tools. It does not include your accounts, database, uploaded images, datasets, model weights, or secrets. A new installation starts with an empty database.

Image upload and preprocessing do not need trained weights. AI inference does: transfer compatible trusted artifacts separately and install optional inference dependencies. This setup does not train or download models automatically.

## Quick setup (Windows, macOS, Linux)

Install Python 3.11–3.13 and Node.js 20+ (including npm). Python 3.11/3.12 are conservative choices for optional AI-library wheel availability. The setup rejects unverified Python 3.14+ rather than attempting an unsupported dependency combination. Internet access is needed for initial dependencies.

```bash
git clone --branch lingareddy-dhanush https://github.com/springboardmentor01092s-tech/Team_2_Artery-Segmentation-DL.git
cd Team_2_Artery-Segmentation-DL
python scripts/setup_local.py
python scripts/run_local.py
```

Use `python3` instead of `python` where needed. On Windows, `py -3.12` can select an installed interpreter. No manual virtual-environment activation is required for these scripts.

Open **http://127.0.0.1:8000**. This launcher serves the built frontend and API together. Use **http://127.0.0.1:8000/docs** for API documentation. Stop it with Ctrl+C.

In a second terminal, verify it with:

```bash
python scripts/check_local.py
```

The setup generates a private JWT secret once, keeps existing configuration unchanged, creates local storage directories, installs backend dependencies, and builds the frontend. Startup creates/migrates the local SQLite schema. Re-run setup after pulling frontend/dependency changes, then restart the application.

## Accounts

Register an account in the app, or optionally run `python scripts/setup_local.py --demo` to seed demo users. Generated passwords are saved only in ignored `backend/demo-credentials.json`. Automatic sharing with the demo team is off by default.

For an administrator without demos, set private `ADMIN_EMAIL` and `ADMIN_PASSWORD` environment variables, then run `backend/.venv/bin/python backend/create_admin.py` on macOS/Linux or `backend\.venv\Scripts\python.exe backend\create_admin.py` on Windows from the repository root. Do not put real passwords in Git. Institutional SSO, Google sign-in, and email reset require their external configuration.

## Optional capabilities

- **AI inference:** run setup with `--with-ai` only if required; it installs large PyTorch-related dependencies. Use the appropriate PyTorch build for your hardware. Compatible checkpoints and selection metadata must be transferred separately; CPU performance may be slow.
- **Scanned PDFs:** install Poppler and ensure `pdftoppm` is on PATH (`brew install poppler` on macOS or `sudo apt install poppler-utils` on Debian/Ubuntu). On Windows, install a trusted Poppler distribution and add its binary directory to PATH.
- **DICOM:** compressed transfer syntaxes may need additional decoding libraries. Unsupported studies return a validation error rather than a fabricated preview.
- **Volumes:** CT/CTA/MRA preparation is separate from X-ray inference. A prepared volume does not imply a connected 3D model.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Missing Python/npm | Install prerequisites and reopen the terminal so PATH updates. |
| Dependency installation fails | Check internet access, supported Python version, available disk space, and library wheel availability. |
| Port 8000 in use | Stop the other process before launching. The built app expects this local port. |
| Models unavailable | Expected without separately installed trusted checkpoints. No training is launched. |
| PDF rejected | Verify Poppler installation with `pdftoppm -v`. |
| No old cases/accounts | Expected on a fresh database. Private data is not copied through Git. |
| Source edits not visible | Re-run setup to rebuild, restart, then refresh the browser. |

The scripts are portable by design, but an actual second Windows/Linux laptop still needs its own smoke test. This local setup is not a production deployment or authorization to use identifiable patient data.
