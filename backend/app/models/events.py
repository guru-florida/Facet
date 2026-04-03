from __future__ import annotations
from typing import Literal
from pydantic import BaseModel
from app.models.track import Track


class TrackAddedEvent(BaseModel):
    type: Literal["track_added"] = "track_added"
    track: Track


class TrackUpdatedEvent(BaseModel):
    type: Literal["track_updated"] = "track_updated"
    track: Track


class TrackRemovedEvent(BaseModel):
    type: Literal["track_removed"] = "track_removed"
    trackId: str


PresenceEvent = TrackAddedEvent | TrackUpdatedEvent | TrackRemovedEvent
