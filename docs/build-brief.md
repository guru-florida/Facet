# Presence Service MVP Build Brief

Build a standalone Presence service for webcam-based presence detection and simple face-based identity recognition.

This service must run independently of the dashboard, but expose APIs that the dashboard can call.

---

## Core design principle

Use a **two-stage pipeline**:

1. **Fast face detection + tracking**
2. **Recognition only for stable faces**

Do NOT run recognition continuously.
Do NOT run heavy processing when no face is present.

The system must be efficient enough to run continuously on low-power devices (e.g., Raspberry Pi 5).

---

## Goals

Create a containerized app with:

- FastAPI backend
- React + TypeScript frontend
- webcam preview
- face detection
- identity recognition (known vs unknown)
- low CPU idle behavior
- leave debounce logic
- REST + WebSocket APIs
- simple standalone UI for setup and verification

---

## Constraints

- Develop first on macOS using the MacBook camera
- Deploy later on Linux (including Raspberry Pi 5)
- No dependency on dashboard internals
- Presence service stores only:
  - identity name
  - identity embedding/template
- Dashboard owns profile mapping

---

## Detection strategy (CRITICAL)

### Stage A: Face detection (always running, lightweight)

Use:
- **MediaPipe Face Detector** (NOT FaceMesh)

Responsibilities:
- detect faces
- return bounding boxes
- assign/update track IDs
- maintain last seen timestamps

Requirements:
- must be fast
- must skip unnecessary work when no faces detected
- must reuse tracking to avoid full detection every frame

---

### Stage B: Recognition (conditional, throttled)

Only run recognition when:

- face has been stable for N frames OR X milliseconds
- face size is above threshold
- detection confidence is above threshold

Recognition must:
- run at a reduced frequency (e.g. every 500ms–2s per track)
- NOT run every frame
- NOT run when no faces exist

---

## Tracking model

Maintain in-memory track objects:

```json
{
  "trackId": "string",
  "status": "unknown | known",
  "identityId": "string | null",
  "displayName": "string | null",
  "confidence": 0.92,
  "firstSeenAt": "...",
  "lastSeenAt": "...",
  "bbox": { "x": 0, "y": 0, "w": 0, "h": 0 },
  "stable": true,
  "leftPending": false
}
