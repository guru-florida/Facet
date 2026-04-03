from __future__ import annotations
from typing import Literal
from pydantic import BaseModel


class BBox(BaseModel):
    x: int
    y: int
    w: int
    h: int


class Track(BaseModel):
    trackId: str
    status: Literal["unknown", "known"] = "unknown"
    identityId: str | None = None
    displayName: str | None = None
    confidence: float = 0.0
    firstSeenAt: str
    lastSeenAt: str
    bbox: BBox
    stable: bool = False
    leftPending: bool = False
