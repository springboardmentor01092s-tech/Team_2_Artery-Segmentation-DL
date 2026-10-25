# Artery AI: Artery Segmentation and Stenosis Detection

Web application for coronary artery analysis from X-ray angiography images,
using deep learning (ARCADE dataset).

## Objective
Build an end-to-end system that manages imaging cases, preprocesses medical
images, segments arteries and detects stenosis.

## Workflow
Upload scan -> Validation -> Normalization -> Noise reduction ->
Contrast enhancement -> ROI extraction -> Model input -> Segmentation ->
Stenosis detection -> Report

## Milestone 1 
- React + FastAPI + SQLite project setup
- JWT authentication with role-based access and audit logging
- Case management (create, view, edit, delete)
- Scan upload and 6-stage preprocessing pipeline
- Design document (architecture, database schema, wireframes)

## Run locally
Backend: cd backend, pip install -r requirements.txt, python -m uvicorn app.main:app --reload
Frontend: cd frontend, npm install, npm run dev