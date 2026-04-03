from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_pipeline, get_track_store
from app.pipeline.pipeline import PresencePipeline
from app.store.track_store import TrackStore

router = APIRouter()


class PipelineStatus(BaseModel):
    running: bool
    fps: float
    frameCount: int
    trackCount: int
    recognizerReady: bool


@router.get("/status", response_model=PipelineStatus)
def get_status(
    pipeline: PresencePipeline = Depends(get_pipeline),
    track_store: TrackStore = Depends(get_track_store),
) -> PipelineStatus:
    return PipelineStatus(
        running=pipeline.running,
        fps=round(pipeline.fps, 1),
        frameCount=pipeline.frame_count,
        trackCount=len(track_store.get_all()),
        recognizerReady=pipeline._recognizer.ready,
    )
