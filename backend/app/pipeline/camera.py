import platform
import queue
import threading
import time
import logging

import cv2
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class CameraCapture:
    """Captures frames from a webcam in a background thread.

    Keeps a queue of size 2 (drop-oldest) so consumers always get
    the latest frame without blocking the capture loop.
    """

    def __init__(self) -> None:
        self._queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=2)
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="camera-capture")
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._thread.start()
        logger.info("Camera capture thread started (index=%d)", settings.camera_index)

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=5)
        logger.info("Camera capture thread stopped")

    def get_latest_frame(self) -> np.ndarray | None:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def _run(self) -> None:
        cap = self._open_camera()
        if cap is None:
            logger.error("Failed to open camera — no frames will be captured")
            return

        try:
            while not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Camera read failed, retrying in 1s")
                    time.sleep(1)
                    continue

                # Drop oldest frame to keep queue fresh
                if self._queue.full():
                    try:
                        self._queue.get_nowait()
                    except queue.Empty:
                        pass
                self._queue.put_nowait(frame)
        finally:
            cap.release()

    def _open_camera(self) -> cv2.VideoCapture | None:
        idx = settings.camera_index
        # On Linux use V4L2 backend for better RPi5 compatibility
        if platform.system() == "Linux":
            cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        else:
            cap = cv2.VideoCapture(idx)

        if not cap.isOpened():
            # Fallback: try default backend
            cap = cv2.VideoCapture(idx)
            if not cap.isOpened():
                return None

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        return cap
