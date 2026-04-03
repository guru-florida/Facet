from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field

from app.config import settings
from app.models.track import BBox, Track
from app.pipeline.detector import Detection


@dataclass
class _TrackState:
    track_id: str
    bbox: BBox
    confidence: float
    first_seen_at: float
    last_seen_at: float
    stable: bool = False
    left_pending: bool = False
    identity_id: str | None = None
    display_name: str | None = None
    recognition_confidence: float = 0.0
    # Internal counters
    seen_frames: int = 1
    missed_frames: int = 0
    last_recognition_at: float = 0.0
    # The raw numpy embedding for this track (set by pipeline)
    _embedding: object = field(default=None, repr=False)


def _iou(a: BBox, b: Detection) -> float:
    ax2, ay2 = a.x + a.w, a.y + a.h
    bx2, by2 = b.x + b.w, b.y + b.h
    ix = max(0, min(ax2, bx2) - max(a.x, b.x))
    iy = max(0, min(ay2, by2) - max(a.y, b.y))
    inter = ix * iy
    if inter == 0:
        return 0.0
    union = a.w * a.h + b.w * b.h - inter
    return inter / union if union > 0 else 0.0


class FaceTracker:
    """Maintains face tracks using greedy IoU matching.

    Track lifecycle:
    - New detection with no IoU match → new track
    - Matched detection → update bbox, increment seen_frames
    - Unmatched existing track → increment missed_frames
      - After N missed frames: leftPending = True
      - After LEAVE_DEBOUNCE_SECONDS: evict
    - stable = True after stability_frames consecutive frames
    """

    IOU_THRESHOLD = 0.3
    MISSED_FRAMES_BEFORE_PENDING = 3

    def __init__(self) -> None:
        self._states: dict[str, _TrackState] = {}

    def update(self, detections: list[Detection]) -> tuple[list[Track], list[str]]:
        """Process a new set of detections.

        Returns:
            (active_tracks, removed_track_ids)
        """
        now = time.monotonic()
        iso_now = _iso_now()

        # Greedy IoU matching
        matched_track_ids: set[str] = set()
        matched_det_indices: set[int] = set()

        if detections and self._states:
            # Build all pairs sorted by IoU descending
            pairs: list[tuple[float, str, int]] = []
            for tid, state in self._states.items():
                for i, det in enumerate(detections):
                    score = _iou(state.bbox, det)
                    if score >= self.IOU_THRESHOLD:
                        pairs.append((score, tid, i))
            pairs.sort(key=lambda p: p[0], reverse=True)

            for _, tid, det_idx in pairs:
                if tid in matched_track_ids or det_idx in matched_det_indices:
                    continue
                matched_track_ids.add(tid)
                matched_det_indices.add(det_idx)
                det = detections[det_idx]
                state = self._states[tid]
                state.bbox = BBox(x=det.x, y=det.y, w=det.w, h=det.h)
                state.confidence = det.confidence
                state.last_seen_at = now
                state.missed_frames = 0
                state.left_pending = False
                state.seen_frames += 1
                if state.seen_frames >= settings.stability_frames:
                    state.stable = True

        # New detections → new tracks
        for i, det in enumerate(detections):
            if i not in matched_det_indices:
                tid = str(uuid.uuid4())[:8]
                self._states[tid] = _TrackState(
                    track_id=tid,
                    bbox=BBox(x=det.x, y=det.y, w=det.w, h=det.h),
                    confidence=det.confidence,
                    first_seen_at=now,
                    last_seen_at=now,
                )

        # Unmatched existing tracks
        removed_ids: list[str] = []
        for tid in list(self._states.keys()):
            if tid in matched_track_ids:
                continue
            state = self._states[tid]
            state.missed_frames += 1
            if state.missed_frames >= self.MISSED_FRAMES_BEFORE_PENDING:
                state.left_pending = True
            # Evict after debounce
            if state.left_pending and (now - state.last_seen_at) >= settings.leave_debounce_seconds:
                del self._states[tid]
                removed_ids.append(tid)

        # Build Track models
        active = [_state_to_track(s, iso_now) for s in self._states.values()]
        return active, removed_ids

    def get_state(self, track_id: str) -> _TrackState | None:
        return self._states.get(track_id)

    def update_recognition(
        self,
        track_id: str,
        identity_id: str | None,
        display_name: str | None,
        confidence: float,
    ) -> Track | None:
        state = self._states.get(track_id)
        if state is None:
            return None
        state.identity_id = identity_id
        state.display_name = display_name
        state.recognition_confidence = confidence
        state.last_recognition_at = time.monotonic()
        return _state_to_track(state, _iso_now())

    def all_states(self) -> list[_TrackState]:
        return list(self._states.values())


def _state_to_track(state: _TrackState, iso_now: str) -> Track:
    from datetime import datetime, timezone
    first_iso = datetime.fromtimestamp(state.first_seen_at, tz=timezone.utc).isoformat()
    last_iso = datetime.fromtimestamp(state.last_seen_at, tz=timezone.utc).isoformat()
    status = "known" if state.identity_id else "unknown"
    return Track(
        trackId=state.track_id,
        status=status,
        identityId=state.identity_id,
        displayName=state.display_name,
        confidence=state.recognition_confidence if state.identity_id else state.confidence,
        firstSeenAt=first_iso,
        lastSeenAt=last_iso,
        bbox=state.bbox,
        stable=state.stable,
        leftPending=state.left_pending,
    )


def _iso_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(tz=timezone.utc).isoformat()
