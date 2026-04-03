# ── Stage 1: Build React frontend ────────────────────────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --frozen-lockfile
COPY frontend/ .
RUN npm run build
# produces /build/dist/


# ── Stage 2: Build + pack client library ─────────────────────────────────────
FROM node:20-alpine AS client-lib-build
WORKDIR /build
COPY client-lib/package.json client-lib/package-lock.json* ./
RUN npm install --frozen-lockfile
COPY client-lib/ .
RUN npm run build
# produces /build/dist/presence-client.js + .d.ts
RUN npm pack
# produces /build/presence-client-*.tgz — rename to fixed filename
RUN mv presence-client-*.tgz presence-client.tgz


# ── Stage 3: Backend + combined serving ──────────────────────────────────────
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
# insightface needs --no-build-isolation (yanked numpy build dep) and g++ to
# compile its face3d Cython extension.  Strip build-essential afterwards.
RUN pip install --no-cache-dir \
    fastapi==0.115.5 \
    "uvicorn[standard]==0.32.1" \
    pydantic==2.9.2 \
    pydantic-settings==2.6.1 \
    opencv-python-headless==4.10.0.84 \
    "mediapipe>=0.10.14" \
    onnxruntime==1.20.1 \
    numpy==1.26.4 \
    python-multipart==0.0.12 \
    "aiofiles==24.1.0" \
 && pip install --no-cache-dir Cython \
 && pip install --no-build-isolation --no-cache-dir insightface==0.7.3 \
 && apt-get purge -y --auto-remove build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY backend/app/ app/

# Frontend SPA — served by FastAPI StaticFiles at /
COPY --from=frontend-build /build/dist/ static/

# Client library tarball — served at /presence-client.tgz
COPY --from=client-lib-build /build/presence-client.tgz static/presence-client.tgz

ENV INSIGHTFACE_HOME=/data/insightface_models
ENV STATIC_DIR=static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
