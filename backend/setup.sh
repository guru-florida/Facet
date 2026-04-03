#!/usr/bin/env bash
# Install backend dependencies, working around insightface's broken build-dep
# (insightface 0.7.3 declares numpy==2.0.0rc1 as a build requirement, which is yanked)
set -e

PIP="${1:-.venv/bin/pip}"

echo "→ Installing base dependencies..."
"$PIP" install \
  "fastapi==0.115.5" \
  "uvicorn[standard]==0.32.1" \
  "pydantic==2.9.2" \
  "pydantic-settings==2.6.1" \
  "opencv-python-headless==4.10.0.84" \
  "mediapipe==0.10.33" \
  "onnxruntime==1.20.1" \
  "numpy==1.26.4" \
  "python-multipart==0.0.12"

echo "→ Installing insightface (--no-build-isolation to bypass broken build dep)..."
"$PIP" install --no-build-isolation "insightface==0.7.3"

echo "✓ All dependencies installed"
