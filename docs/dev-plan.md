# Presence Service — Dev Plan

## Overview

Standalone webcam-based presence detection service. Runs independently of any dashboard. Detects faces, tracks them over time, and recognises known identities via a two-stage pipeline.

**Core design:** Stage A (face detection, every frame, lightweight) → Stage B (ArcFace recognition, throttled per stable track).

---

## Phase 1 — Camera + Video WebSocket ✅

**Goal:** Browser sees live camera feed. No ML yet.

- FastAPI app with `lifespan` context manager
- `CameraCapture` background thread — OpenCV `VideoCapture`, drop-oldest `Queue(maxsize=2)`
- `config.py` — all tunables via env vars (pydantic-settings)
- `store/db.py` — SQLite schema init (`identities`, `embeddings`)
- `ws/video_ws.py` — JPEG-encode frames → binary WebSocket at 15 fps cap
- Frontend scaffold — Vite + React + TypeScript + MUI, `useVideoSocket` hook, `VideoFeed` component

---

## Phase 2 — Stage A: Face Detection + Tracking ✅

**Goal:** Bounding boxes on video; persistent track IDs; `/api/presence` returns live tracks.

- `pipeline/detector.py` — MediaPipe Tasks API (`FaceDetector`, `blaze_face_short_range.tflite`); model downloaded on first run
- `pipeline/tracker.py` — greedy IoU match; `Track` dataclass per spec; `stable` after 8 frames; `leftPending` after 3 missed frames; evict after `LEAVE_DEBOUNCE_SECONDS`
- `store/track_store.py` — thread-safe in-memory track dict
- `pipeline/pipeline.py` — main loop thread; Stage A every frame; annotated frames to video WS
- `api/presence.py`, `api/status.py` — first REST endpoints

---

## Phase 3 — Stage B: Recognition + Identity Store ✅

**Goal:** Stable tracks get recognised; enroll via API; tracks report `known` status.

- `pipeline/recognizer.py` — insightface `buffalo_sc` downloaded via `FaceAnalysis`; ArcFace model (`w600k_mbf.onnx`) called directly via onnxruntime to avoid double-detection on tight crops; 512-d cosine similarity match
- `store/identity_repo.py` — identity + embedding CRUD; embeddings stored as numpy BLOBs; in-memory cache rebuilt on every mutation
- `pipeline/pipeline.py` Stage B — per-track throttle: `stable` AND `bbox.w > MIN_FACE_PX` AND `confidence > threshold` AND `time since last recognition > RECOGNITION_INTERVAL`
- `ws/presence_ws.py` — `ConnectionManager`; pipeline → asyncio bridge via `call_soon_threadsafe`; typed event envelopes (`track_added`, `track_updated`, `track_removed`)

---

## Phase 4 — Full REST API + React UI ✅

**Goal:** Complete enrollment and identity management UI; polished MUI layout.

- `api/identities.py` — `POST /api/identities` (enroll from best stable face), `POST /api/identities/{id}/samples` (add sample), `DELETE /api/identities/{id}`
- `src/api/types.ts` — strict TypeScript types, no `any`
- `hooks/usePresenceSocket.ts` — `Map<trackId, Track>` maintained from WS events, auto-reconnect
- `hooks/useVideoSocket.ts` — binary frames → revocable Blob URLs
- Components: `VideoFeed`, `TrackList`, `EnrollDialog`, `IdentityManager`, `StatusBar`
- Layout: two-column MUI grid — left: video + active faces; right: identities + API reference

---

## Phase 5 — Docker ✅

**Goal:** Single `docker-compose up` deploys on Linux/RPi5.

- `backend/Dockerfile` — `python:3.11-slim`, pre-installs deps, sets `INSIGHTFACE_HOME=/data/models`
- `frontend/Dockerfile` — multi-stage (`node:20-alpine` build → `nginx:alpine` serve), nginx proxies `/api/` and `/ws/` to backend
- `docker-compose.yml` — `devices: [/dev/video0]` for camera passthrough, `./data` volume for SQLite + models
- `docker-compose.dev.yml` — macOS override: removes `devices` block (Docker Desktop cannot access MacBook camera)
- `backend/setup.sh` — installs deps in correct order; insightface requires `--no-build-isolation` due to yanked `numpy==2.0.0rc1` build dep

**macOS dev:** run backend + frontend natively (see README). Use Docker only for Linux/RPi5 deployment.

---

## Known Issues / Resolved

| Issue | Resolution |
|---|---|
| `mediapipe==0.10.14` not available on Python 3.13 | Pinned to `0.10.33` |
| `mp.solutions.face_detection` removed in mediapipe 0.10+ | Rewrote to MediaPipe Tasks API |
| SSL cert failure downloading mediapipe model on macOS | Fallback to unverified context on `urllib.error.URLError` |
| `insightface` build fails: `numpy==2.0.0rc1` yanked | Install with `--no-build-isolation` via `setup.sh` |
| Enrollment 422: `FaceAnalysis.get()` re-runs detection on 112×112 tight crop → no faces found | Call ArcFace onnx model directly via onnxruntime; bypass `FaceAnalysis.get()` |

---

## Phase 6 — Presence Event Log + Outbound Webhooks (proposed)

**Goal:** Record who was present and when; push events to external consumers (e.g. a dashboard) without polling.

### Presence log

Add a `presence_events` table:

```sql
CREATE TABLE presence_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,   -- 'arrived' | 'left'
    identity_id TEXT,           -- NULL if unknown
    display_name TEXT,
    track_id TEXT NOT NULL,
    confidence REAL,
    occurred_at TEXT NOT NULL
);
```

New endpoints:
- `GET /api/events?since=<iso>&limit=100` — paginated log for dashboard polling
- `DELETE /api/events` — clear log

### Outbound webhooks

Config: `WEBHOOK_URL` env var (optional). When set, POST a JSON payload on every `track_added` / `track_removed` event:

```json
{
  "type": "arrived",
  "identityId": "abc",
  "displayName": "Alice",
  "confidence": 0.91,
  "occurredAt": "2026-04-02T21:00:00Z"
}
```

Delivery: fire-and-forget from the asyncio broadcast loop; log failures but don't retry (dashboard can catch up via `GET /api/events`).

---

## Running Locally (macOS)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
bash setup.sh
uvicorn app.main:app --reload --port 8000

# second terminal
cd frontend && npm install && npm run dev
# → http://localhost:5173
```

On first run, two models are downloaded automatically:
- `blaze_face_short_range.tflite` (~800 KB) — MediaPipe face detector
- `buffalo_sc/` (~300 MB) — insightface ArcFace models

## Deployment (Linux / RPi5)

```bash
docker-compose up --build
# → http://<host>:3000
```

Ensure `/dev/video0` exists and the user running Docker has camera access (`sudo usermod -aG video $USER`).
