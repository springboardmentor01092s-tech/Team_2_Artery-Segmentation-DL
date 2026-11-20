FROM node:22-bookworm-slim AS web
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim-trixie AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend \
    DATABASE_URL=sqlite:////data/artery.db STORAGE_DIR=/data/storage \
    COROVISION_ENV=production COROVISION_TRAINED_RELEASE=/models/trained_release \
    COROVISION_MODEL_PROVIDER=preserved COROVISION_INFERENCE_WORKER=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0t64 libgomp1 poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 corovision && useradd --uid 10001 --gid 10001 --create-home corovision \
    && mkdir -p /data/storage /models && chown -R 10001:10001 /data /models
COPY backend/requirements*.txt /app/backend/
RUN python -m pip install --no-cache-dir pip==26.3 setuptools==84.2.1
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r backend/requirements-ai.txt
COPY backend/app/ /app/backend/app/
COPY backend/create_admin.py /app/backend/create_admin.py
COPY scripts/install_trained_release.py /app/scripts/install_trained_release.py
COPY deploy/start.sh /app/deploy/start.sh
COPY ml/ /app/ml/
ARG COROVISION_MODEL_ARCHIVE_URL=https://github.com/springboardmentor01092s-tech/Team_2_Artery-Segmentation-DL/releases/download/corovision-mask-models-v1/CoroVision_application_mask_models_v1.zip
RUN MODEL_URL="$COROVISION_MODEL_ARCHIVE_URL" python -c "import os,urllib.request; urllib.request.urlretrieve(os.environ['MODEL_URL'], '/tmp/corovision-models.zip')" \
    && python /app/scripts/install_trained_release.py --install /tmp/corovision-models.zip \
    && rm -f /tmp/corovision-models.zip \
    && chown -R 10001:10001 /models
COPY --from=web /build/frontend/dist/ /app/frontend/dist/
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health/ready',timeout=4)"
CMD ["/app/deploy/start.sh"]
