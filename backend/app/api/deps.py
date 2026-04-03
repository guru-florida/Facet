"""FastAPI dependency injection."""
from typing import Annotated

from fastapi import Request

from app.pipeline.pipeline import PresencePipeline
from app.pipeline.recognizer import FaceRecognizer
from app.store.identity_repo import IdentityRepo
from app.store.track_store import TrackStore


def get_track_store(request: Request) -> TrackStore:
    return request.app.state.track_store


def get_identity_repo(request: Request) -> IdentityRepo:
    return request.app.state.identity_repo


def get_pipeline(request: Request) -> PresencePipeline:
    return request.app.state.pipeline


def get_recognizer(request: Request) -> FaceRecognizer:
    return request.app.state.recognizer
