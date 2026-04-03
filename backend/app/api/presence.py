from fastapi import APIRouter, Depends

from app.api.deps import get_track_store
from app.models.track import Track
from app.store.track_store import TrackStore

router = APIRouter()


@router.get("/presence", response_model=list[Track])
def get_presence(track_store: TrackStore = Depends(get_track_store)) -> list[Track]:
    """Return all currently active face tracks."""
    return track_store.get_all()
