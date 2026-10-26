FROM node:22-bookworm-slim AS web
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend \
    DATABASE_URL=sqlite:////data/artery.db STORAGE_DIR=/data/storage \
    COROVISION_ENV=production COROVISION_TRAINED_RELEASE=/models \
    COROVISION_MODEL_PROVIDER=preserved COROVISION_INFERENCE_WORKER=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 libgomp1 poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 corovision && useradd --uid 10001 --gid 10001 --create-home corovision \
    && mkdir -p /data/storage /models && chown -R 10001:10001 /data /models
COPY backend/requirements*.txt /app/backend/
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r backend/requirements-ai.txt
COPY backend/app/ /app/backend/app/
COPY backend/create_admin.py /app/backend/create_admin.py
COPY ml/ /app/ml/
COPY --from=web /build/frontend/dist/ /app/frontend/dist/
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health/ready',timeout=4)"
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log", "--log-config", "/app/backend/app/logging.json"]
