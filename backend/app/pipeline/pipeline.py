"""Main pipeline orchestrator.

Runs in a background threading.Thread.
Stage A: detect → track (every frame)
Stage B: recognize stable faces (throttled per track)
"""
from __future__ import annotations
import logging
import threading
import time

import cv2
import numpy as np

from app.config import settings
from app.pipeline.camera import CameraCapture
from app.pipeline.detector import FaceDetector
from app.pipeline.recognizer import FaceRecognizer
from app.pipeline.tracker import FaceTracker
from app.store.identity_repo import IdentityRepo
from app.store.track_store import TrackStore
from app.ws.video_ws import get_active_client_count, set_latest_frame

logger = logging.getLogger(__name__)

_BBOX_COLORS = {
    "unknown": (0, 165, 255),  # orange
    "known": (0, 200, 80),     # green
}


class PresencePipeline:
    def __init__(
        self,
        camera: CameraCapture,
        track_store: TrackStore,
        identity_repo: IdentityRepo,
        recognizer: FaceRecognizer,
        presence_publish_fn: object,  # callable(dict) — bridges to asyncio
    ) -> None:
        self._camera = camera
        self._track_store = track_store
        self._identity_repo = identity_repo
        self._recognizer = recognizer
        self._publish = presence_publish_fn

        self._detector = FaceDetector()
        self._tracker = FaceTracker()

        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="pipeline")

        self._fps: float = 0.0
        self._frame_count: int = 0
        self._running: bool = False

    def start(self) -> None:
        self._running = True
        self._thread.start()
        logger.info("Pipeline started")

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=10)
        self._detector.close()
        self._running = False
        logger.info("Pipeline stopped")

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def running(self) -> bool:
        return self._running

    @property
    def frame_count(self) -> int:
        return self._frame_count

    def _run(self) -> None:
        fps_window = 30
        frame_times: list[float] = []

        while not self._stop_event.is_set():
            target_fps = (
                settings.pipeline_fps_streaming
                if get_active_client_count() > 0
                else settings.pipeline_fps_idle
            )
            target_interval = 1.0 / target_fps

            frame = self._camera.get_latest_frame()
            if frame is None:
                time.sleep(0.01)
                continue

            t_start = time.monotonic()

            try:
                self._process_frame(frame)
            except Exception:
                logger.exception("Unhandled exception in pipeline frame — continuing")

            # ── FPS tracking ─────────────────────────────────────────────────
            elapsed = time.monotonic() - t_start
            frame_times.append(elapsed)
            if len(frame_times) > fps_window:
                frame_times.pop(0)
            if frame_times:
                avg = sum(frame_times) / len(frame_times)
                self._fps = 1.0 / avg if avg > 0 else 0.0
            self._frame_count += 1

            # ── Rate limiting ─────────────────────────────────────────────────
            sleep_for = target_interval - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

        self._running = False

    def _process_frame(self, frame: np.ndarray) -> None:
        # ── Stage A: Detect + Track ──────────────────────────────────────────
        detections = self._detector.detect(frame)
        active_tracks, removed_ids = self._tracker.update(detections)

        # Sync track store and publish events
        existing_ids = {t.trackId for t in self._track_store.get_all()}
        for track in active_tracks:
            is_new = track.trackId not in existing_ids
            self._track_store.upsert(track)
            if is_new:
                self._publish({"type": "track_added", "track": track.model_dump()})

        for tid in removed_ids:
            self._track_store.remove(tid)
            self._publish({"type": "track_removed", "trackId": tid})

        # ── Stage B: Recognition (throttled) ────────────────────────────────
        if self._recognizer.ready and active_tracks:
            known_embeddings = self._identity_repo.get_embeddings()
            if known_embeddings:
                self._run_recognition(frame, active_tracks, known_embeddings)

        # ── Annotate frame for video WS ──────────────────────────────────────
        annotated = self._annotate(frame, active_tracks)
        set_latest_frame(annotated)

    def _run_recognition(
        self,
        frame: np.ndarray,
        active_tracks: list,
        known_embeddings: dict,
    ) -> None:
        now = time.monotonic()
        for track in active_tracks:
            if track.leftPending:
                continue
            if not track.stable:
                continue
            if track.bbox.w < settings.min_face_px:
                continue
            if track.confidence < settings.recognition_confidence:
                continue

            state = self._tracker.get_state(track.trackId)
            if state is None:
                continue
            if (now - state.last_recognition_at) < settings.recognition_interval:
                continue

            # Extract face crop
            h, w = frame.shape[:2]
            x1 = max(0, track.bbox.x)
            y1 = max(0, track.bbox.y)
            x2 = min(w, track.bbox.x + track.bbox.w)
            y2 = min(h, track.bbox.y + track.bbox.h)
            if x2 <= x1 or y2 <= y1:
                continue
            crop = frame[y1:y2, x1:x2]

            embedding = self._recognizer.get_embedding(crop)
            if embedding is None:
                state.last_recognition_at = now
                continue

            identity_id, score = self._recognizer.match(embedding, known_embeddings)
            display_name = self._identity_repo.get_name(identity_id) if identity_id else None

            updated_track = self._tracker.update_recognition(
                track.trackId, identity_id, display_name, score
            )
            if updated_track:
                self._track_store.upsert(updated_track)
                self._publish({"type": "track_updated", "track": updated_track.model_dump()})

    @staticmethod
    def _annotate(frame: np.ndarray, tracks: list) -> np.ndarray:
        out = frame.copy()
        for track in tracks:
            if track.leftPending:
                continue
            color = _BBOX_COLORS.get(track.status, (200, 200, 200))
            x, y, w, h = track.bbox.x, track.bbox.y, track.bbox.w, track.bbox.h
            cv2.rectangle(out, (x, y), (x + w, y + h), color, 2)
            label = track.displayName if track.displayName else f"#{track.trackId}"
            cv2.putText(out, label, (x, max(y - 8, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
        return out
