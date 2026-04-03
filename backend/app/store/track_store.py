import threading
from app.models.track import Track


class TrackStore:
    def __init__(self) -> None:
        self._tracks: dict[str, Track] = {}
        self._lock = threading.Lock()

    def get_all(self) -> list[Track]:
        with self._lock:
            return list(self._tracks.values())

    def get(self, track_id: str) -> Track | None:
        with self._lock:
            return self._tracks.get(track_id)

    def upsert(self, track: Track) -> None:
        with self._lock:
            self._tracks[track.trackId] = track

    def remove(self, track_id: str) -> None:
        with self._lock:
            self._tracks.pop(track_id, None)

    def get_best_stable_face(self) -> Track | None:
        """Return the largest stable face currently tracked."""
        with self._lock:
            stable = [t for t in self._tracks.values() if t.stable and not t.leftPending]
        if not stable:
            return None
        return max(stable, key=lambda t: t.bbox.w * t.bbox.h)
