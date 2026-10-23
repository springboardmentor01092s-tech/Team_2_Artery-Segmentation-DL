# CoroVision AI

Role-specific navigation, implemented sections, outstanding modules and dashboard
counting definitions are documented in the
[16 October role section map](docs/ROLE_SECTIONS_ROUTE_MATRIX_2026-10-16.md).

**Advanced Coronary Artery Segmentation and Stenosis Analysis Platform**

*See the vessels. Detect the narrowing. Understand the results.*

**Academic title:** CoroVision AI: An Explainable Deep Learning Platform for
Coronary Artery Segmentation, Vessel Structure Analysis, and Stenosis Detection

**Suggested repository name:** `CoroVision-AI` · **Project group:** Group 3

Milestone 1 (weeks 1–2) foundation for a research prototype using 2D coronary
X-ray angiography and the public ARCADE dataset. This milestone includes data
inspection, documented scope and architecture, authentication and account
management, de-identified case management, image upload, and a 512×512
preprocessing preview.
An optional research-only neural baseline provides artery and suspected stenosis
mask overlays after local training. It is not a diagnosis or severity estimate.
See [AI analysis](docs/AI_ANALYSIS.md) for training and validation limits.
See [frontend workflow](docs/FRONTEND_WORKFLOW.md) for navigation, role access, reports, and current model limitations.
See [case management and preprocessing](docs/CASE_AND_PREPROCESSING.md) for
de-identified metadata, analysis history, ROI/frame selection, and modality limits.

## Repository layout

- `arcade/`: downloaded ARCADE dataset; not needed to launch the app.
- `scripts/dataset_audit.py`: read-only inventory and integrity checks.
- `docs/`: project scope, dataset EDA, system architecture/schema, and UI wireframes.
- `backend/`: FastAPI, SQLAlchemy, authentication, case and image APIs.
- `frontend/`: React and TypeScript app.
- `storage/`: local uploaded files and processed previews (ignored by Git).

The frontend uses adapted Button, Input, Label, Card, and theme code from
[Codehagen/Prismui](https://github.com/Codehagen/Prismui). See
`frontend/THIRD_PARTY_NOTICES.md` and `frontend/LICENSE.prismui.md`
for source and license details.

## Run locally

Requires Python 3.11+ and Node.js 20+.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
uvicorn app.main:app --reload
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. API documentation is at
`http://localhost:8000/docs`. The default local database is SQLite at
`artery.db`. To use PostgreSQL, install the listed `psycopg` dependency and
set `DATABASE_URL=postgresql+psycopg://user:password@host:5432/database`.

Open the `http://localhost:5173` URL in a browser while both terminal
commands are running. Opening `frontend/index.html` as a `file://` page
will not start Vite or the API and will appear broken.

For a local demo, register a researcher account, create a pseudonymous case
code, and upload multiple supported raster images, DICOM studies, or scanned
PDF pages (up to 50 MB each). The app processes each selected file separately:
validation, grayscale conversion, intensity normalization, median noise
reduction, contrast enhancement, optional ROI cropping, and a padded 512×512
preview. Standard upload preserves image intensity apart from conversion needed
for grayscale and high-bit-depth data. Research-only median denoising and
clipped autocontrast are optional and off by default. DICOM multi-frame studies
need a frame index; PDFs default to page zero and require Poppler's `pdftoppm`
on the server. Unsupported transfer
syntaxes and document types return a validation error. Upload only public or
de-identified images. See [the exact formats and limits](docs/CASE_AND_PREPROCESSING.md).

To bootstrap a local administrator, set `ADMIN_EMAIL` and `ADMIN_PASSWORD`
(12+ characters) and run `python3 create_admin.py` from `backend/`. Only an
administrator can grant clinician, ML engineer, or administrator roles through
the Administration screen or admin API. Public registration always creates a
researcher account. The Profile & security screen supports profile edits,
password changes, session review, sign-out, and personal audit history.

Username and email password sign-in, Google/GitHub OAuth, and email
password reset setup are documented in [Authentication setup](docs/AUTH_SETUP.md).
External provider credentials are required for live social sign-in and code
delivery; see `backend/.env.example` for variable names.

## Dataset audit

```bash
python3 scripts/dataset_audit.py
```

This checks annotation references, file counts, empty polygons, class counts,
and identical-image overlap across train/validation/test.

## Backend tests

```bash
cd backend
pytest -q
```

The tests exercise registration, login, authorization, case creation, upload
validation, and preview generation.

## Current limitations

The auth and storage implementation is suitable for a local student prototype.
Before accepting real patient images or public deployment, add institution
managed role assignment, migration scripts, rate limits, TLS, secret management,
backup policy, audit review, and an approved privacy/security process.
