FROM python:3.11-slim

# OpenCV headless needs these system libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download insightface models at build time
# Set home so models go to /data/insightface_models (volume-mounted)
# On first build this pulls ~200MB; cached in subsequent builds via volume
ENV INSIGHTFACE_HOME=/data/insightface_models

COPY app/ app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
