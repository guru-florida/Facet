"""
presence.identity interface implementation.

Exposes the real-time track stream and a REST snapshot endpoint.

MacBoard proxy pattern:
  GET /api/adapters/{id}/interfaces/presence.identity/tracks
      → this adapter's GET /api/interfaces/presence.identity/tracks

  WS  /api/adapters/{id}/interfaces/presence.identity/ws/presence
      → this adapter's /ws/interfaces/presence.identity/presence
"""
from fastapi import APIRouter, Depends

from app.api.deps import get_track_store
from app.models.track import Track
from app.store.track_store import TrackStore

# ---------------------------------------------------------------------------
# Interface metadata — declared by GET /api/adapter
# ---------------------------------------------------------------------------

INTERFACE_META = {
    "interface": "presence.identity",
    "version": "1",
    "name": "Person Detection",
    "websockets": [
        {
            "path": "/ws/interfaces/presence.identity/presence",
            "type": "presence_events",
            "description": "Live JSON stream of track add/update/remove events",
        }
    ],
}

# ---------------------------------------------------------------------------
# REST router — mounted at /api/interfaces/presence.identity
# ---------------------------------------------------------------------------

router = APIRouter()


@router.get("/tracks", response_model=list[Track])
def get_tracks(track_store: TrackStore = Depends(get_track_store)) -> list[Track]:
    """Return all currently active face tracks."""
    return track_store.get_all()
