# Artery Segmentation and Stenosis Detection Using Advanced Deep Learning Techniques

A web application for coronary angiography. A clinician uploads an X-ray angiogram, the system cleans the image, segments the arteries with deep learning, extracts the vessel centerline and measures vessel diameter. Narrowing of a vessel (stenosis) is the clinical sign this project works towards detecting.

> Student project and decision-support prototype. It is not a certified medical device.

## Project status

| Milestone | Weeks | Focus | Status |
|---|---|---|---|
| 1 | 1-2 | Setup, dataset, EDA, design, authentication, case management, image upload, preprocessing | Done (profile page and audit log screen still open) |
| 2 | 3-4 | Artery segmentation, centerline, vessel diameter, model comparison | Done |
| 3 | 5-6 | Stenosis detection, severity grading, explainable AI | Planned |
| 4 | 7-8 | Reports, testing, Docker, deployment | Planned |

## Tech stack

- **Backend:** FastAPI, SQLite, JWT authentication
- **Frontend:** React, Vite, Tailwind CSS, axios
- **Deep learning:** PyTorch (U-Net and Attention U-Net), trained on Google Colab (T4 GPU)
- **Image analysis:** NumPy and SciPy (no scikit-image)
- **Dataset:** ARCADE (2D X-ray coronary angiography)

## Milestone 1: Foundation

- **Dataset:** ARCADE downloaded and organised into the `syntax` and `stenosis` tasks, each with train, validation and test splits.
- **EDA:** `eda/explore_arcade.py` explores the dataset and writes sample annotation images and a summary to `eda_output/`.
- **Design documents (`docs/`):** system architecture, database schema and UI wireframes.
- **Backend:** FastAPI service with SQLite.
  - Authentication: register, login and current user (`/auth/register`, `/auth/login`, `/auth/me`) with JWT tokens.
  - Roles: clinician and patient.
  - Case management: create and list patient cases, and upload an X-ray to a case.
- **Preprocessing pipeline:** the Preprocess button shows the image after each stage, so the input is standardised before it reaches the model.
- **Frontend:** login, register and a professional dashboard with case list and image upload.

## Milestone 2: Artery segmentation

### What was built

1. **Baseline model:** U-Net (base 32 filters), trained for both tasks.
2. **Advanced model:** Attention U-Net (attention gates on the skip connections), trained for both tasks.
3. **Training and evaluation:** Colab T4 GPU, 256x256 input, batch size 8, learning rate 1e-3, 30 epochs. The best epoch is chosen by validation Dice, and the test set is used once at the end.
4. **Mask generation:** `POST /cases/{id}/segment` (task `syntax` or `stenosis`) runs CPU inference and returns the mask and an overlay.
5. **Post-processing:** removes small noise and edge artifacts (border guard and bar filter).
6. **Vessel structure extraction:** finds the connected vessel segments.
7. **Centerline extraction:** thins each vessel to a one-pixel line along its middle.
8. **Vessel diameter estimation:** a distance transform along the centerline gives mean, maximum and minimum diameter in pixels.
9. **Dashboard integration:** Segment button, result panel (overlay, mask, centerline, vessel numbers, syntax/stenosis toggle), a "segmented" badge on each case and a Results button that reopens saved results from the database.
10. **Model comparison and report:** see below and the performance report in `docs/`.

### Test results (threshold 0.5, 256x256)

| Task | U-Net Dice | Attention U-Net Dice |
|---|---|---|
| Syntax (artery segments) | 0.7597 | 0.7509 |
| Stenosis (narrowed regions) | 0.4888 | 0.478 |

The two models perform almost the same. The **U-Net is used in the app**: it scored slightly higher, has a simpler architecture and runs fast on CPU. The Attention U-Net is kept as the advanced architecture that was implemented and compared. Full metrics (Dice, IoU, precision, recall, specificity, pixel accuracy) are in `results/results_summary.json`.

Stenosis scores are lower because the narrowed regions are very small and the classes are heavily imbalanced.

### Segmentation pipeline in the app

Upload, preprocess, segment with U-Net, clean the mask, extract the centerline, measure diameters. Diameters are in pixels, because the dataset gives no pixel spacing for conversion to millimetres.

## Project structure

```
artery_app/
├── backend/        FastAPI app, model loading (ml.py), vessel analysis (analysis.py)
├── frontend/       React + Vite + Tailwind dashboard
├── eda/            Dataset exploration script
├── eda_output/     EDA figures and summary
├── notebooks/      Colab training notebook
├── results/        Saved test metrics
├── docs/           Design documents and Milestone 2 performance report
├── models/         best_syntax.pt and best_stenosis.pt (not stored in git)
└── data/           ARCADE dataset (not stored in git)
```

## Model weights

Weights are not stored in the repository. Download them from the GitHub release `milestone2-models-v1` and place the `.pt` files in `models/`:

- `best_syntax.pt`
- `best_stenosis.pt`

## Run locally

**Backend** (from `backend/`):

```powershell
python -m uvicorn app.main:app --reload
```

The API runs at http://127.0.0.1:8000 and interactive docs are at http://127.0.0.1:8000/docs.

**Frontend** (from `frontend/`):

```powershell
npm install
npm run dev
```

Open http://localhost:5173.

## Limitations

- Stenosis Dice (about 0.49) can be improved with higher resolution (512 px), stronger augmentation, starting from the syntax weights and threshold tuning on the validation set.
- Diameters are in pixels, not millimetres.
- The model is trained on one public dataset and has not been clinically validated.