"""
presence.identity.enrollment interface implementation.

Exposes identity CRUD, pipeline status, and a live video stream.

MacBoard proxy pattern:
  GET    /api/adapters/{id}/interfaces/presence.identity.enrollment/identities
  POST   /api/adapters/{id}/interfaces/presence.identity.enrollment/identities
  POST   /api/adapters/{id}/interfaces/presence.identity.enrollment/identities/{id}/samples
  DELETE /api/adapters/{id}/interfaces/presence.identity.enrollment/identities/{id}
  GET    /api/adapters/{id}/interfaces/presence.identity.enrollment/status

  WS  /api/adapters/{id}/interfaces/presence.identity.enrollment/ws/video
      → this adapter's /ws/interfaces/presence.identity.enrollment/video
"""
from __future__ import annotations

import logging

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_identity_repo, get_pipeline, get_recognizer, get_track_store
from app.models.identity import Identity
from app.pipeline.pipeline import PresencePipeline
from app.pipeline.recognizer import FaceRecognizer
from app.store.identity_repo import IdentityRepo
from app.store.track_store import TrackStore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Interface metadata — declared by GET /api/adapter
# ---------------------------------------------------------------------------

INTERFACE_META = {
    "interface": "presence.identity.enrollment",
    "version": "1",
    "name": "Person Enrollment",
    "websockets": [
        {
            "path": "/ws/interfaces/presence.identity.enrollment/video",
            "type": "video_jpeg",
            "description": "Live JPEG video stream for enrollment UI",
        }
    ],
}

# ---------------------------------------------------------------------------
# Request/response schemas
# ---------------------------------------------------------------------------

class CreateIdentityRequest(BaseModel):
    name: str


class PipelineStatusResponse(BaseModel):
    running: bool
    fps: float
    frameCount: int
    trackCount: int
    recognizerReady: bool

# ---------------------------------------------------------------------------
# REST router — mounted at /api/interfaces/presence.identity.enrollment
# ---------------------------------------------------------------------------

router = APIRouter()


@router.get("/identities", response_model=list[Identity])
def list_identities(repo: IdentityRepo = Depends(get_identity_repo)) -> list[Identity]:
    return repo.list_identities()


@router.post("/identities", response_model=Identity, status_code=status.HTTP_201_CREATED)
def create_identity(
    body: CreateIdentityRequest,
    repo: IdentityRepo = Depends(get_identity_repo),
    recognizer: FaceRecognizer = Depends(get_recognizer),
    track_store: TrackStore = Depends(get_track_store),
) -> Identity:
    """Create a new identity by capturing an embedding from the current best stable face."""
    if not recognizer.ready:
        raise HTTPException(status_code=503, detail="Recognizer not ready yet")

    best_track = track_store.get_best_stable_face()
    if best_track is None:
        raise HTTPException(
            status_code=422,
            detail="No stable face detected. Position your face in the frame and try again.",
        )

    from app.ws.video_ws import _latest_frame
    frame = _latest_frame
    if frame is None:
        raise HTTPException(status_code=503, detail="No camera frame available")

    crop = _extract_crop(frame, best_track.bbox)
    if crop is None:
        raise HTTPException(status_code=422, detail="Could not extract face crop from frame")

    embedding = recognizer.get_embedding(crop)
    if embedding is None:
        raise HTTPException(
            status_code=422,
            detail="Could not compute face embedding. Ensure face is clearly visible.",
        )

    identity = repo.create_identity(body.name)
    repo.add_embedding(identity.id, embedding)
    logger.info("Created identity %s (%s)", identity.name, identity.id)
    return identity


@router.post(
    "/identities/{identity_id}/samples",
    response_model=Identity,
    status_code=status.HTTP_200_OK,
)
def add_sample(
    identity_id: str,
    repo: IdentityRepo = Depends(get_identity_repo),
    recognizer: FaceRecognizer = Depends(get_recognizer),
    track_store: TrackStore = Depends(get_track_store),
) -> Identity:
    """Add another face embedding sample to an existing identity."""
    identities = repo.list_identities()
    identity = next((i for i in identities if i.id == identity_id), None)
    if identity is None:
        raise HTTPException(status_code=404, detail="Identity not found")

    if not recognizer.ready:
        raise HTTPException(status_code=503, detail="Recognizer not ready yet")

    best_track = track_store.get_best_stable_face()
    if best_track is None:
        raise HTTPException(status_code=422, detail="No stable face detected")

    from app.ws.video_ws import _latest_frame
    frame = _latest_frame
    if frame is None:
        raise HTTPException(status_code=503, detail="No camera frame available")

    crop = _extract_crop(frame, best_track.bbox)
    if crop is None:
        raise HTTPException(status_code=422, detail="Could not extract face crop")

    embedding = recognizer.get_embedding(crop)
    if embedding is None:
        raise HTTPException(status_code=422, detail="Could not compute face embedding")

    repo.add_embedding(identity_id, embedding)
    updated = next(i for i in repo.list_identities() if i.id == identity_id)
    return updated


@router.delete(
    "/identities/{identity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def delete_identity(
    identity_id: str,
    repo: IdentityRepo = Depends(get_identity_repo),
) -> None:
    if not repo.delete_identity(identity_id):
        raise HTTPException(status_code=404, detail="Identity not found")


@router.get("/status", response_model=PipelineStatusResponse)
def get_status(
    pipeline: PresencePipeline = Depends(get_pipeline),
    track_store: TrackStore = Depends(get_track_store),
) -> PipelineStatusResponse:
    return PipelineStatusResponse(
        running=pipeline.running,
        fps=round(pipeline.fps, 1),
        frameCount=pipeline.frame_count,
        trackCount=len(track_store.get_all()),
        recognizerReady=pipeline._recognizer.ready,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_crop(frame: np.ndarray, bbox: object) -> np.ndarray | None:
    h, w = frame.shape[:2]
    x1 = max(0, bbox.x)
    y1 = max(0, bbox.y)
    x2 = min(w, bbox.x + bbox.w)
    y2 = min(h, bbox.y + bbox.h)
    if x2 <= x1 or y2 <= y1:
        return None
    return frame[y1:y2, x1:x2]
