from __future__ import annotations
import logging
import os
import ssl
import urllib.request
from dataclasses import dataclass

import cv2
import mediapipe as mp
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

# MediaPipe 0.10+ uses the Tasks API; the legacy mp.solutions namespace is gone.
# The short-range blaze face model is ~800KB and is downloaded once.
_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_detector/"
    "blaze_face_short_range/float16/latest/blaze_face_short_range.tflite"
)
_MODEL_FILENAME = "blaze_face_short_range.tflite"


def _download(url: str, dest: str) -> None:
    """Download url to dest, falling back to unverified SSL on macOS cert issues.

    macOS Python.org installs often lack system CA certs, causing SSL failures.
    The fallback is safe here — we're downloading a known model from Google Storage.
    urllib.error.URLError wraps the underlying ssl.SSLCertVerificationError.
    """
    try:
        urllib.request.urlretrieve(url, dest)
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(url, context=ctx) as resp, open(dest, "wb") as f:
            f.write(resp.read())


@dataclass
class Detection:
    x: int
    y: int
    w: int
    h: int
    confidence: float


class FaceDetector:
    """Wraps MediaPipe Face Detector (Tasks API, Stage A).

    Uses the short-range blaze face model — fast and appropriate for webcam use.
    The Tasks API returns absolute pixel bounding boxes, not normalised coords.
    """

    def __init__(self) -> None:
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision

        model_path = self._ensure_model()
        base_options = mp_python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceDetectorOptions(
            base_options=base_options,
            min_detection_confidence=settings.detection_confidence,
        )
        self._detector = vision.FaceDetector.create_from_options(options)
        logger.info("MediaPipe FaceDetector loaded (Tasks API, model=%s)", model_path)

    @staticmethod
    def _ensure_model() -> str:
        model_dir = os.path.join(os.path.dirname(settings.db_path), "mediapipe_models")
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, _MODEL_FILENAME)
        if not os.path.exists(model_path):
            logger.info("Downloading MediaPipe face detector model to %s …", model_path)
            _download(url=_MODEL_URL, dest=model_path)
            logger.info("Model downloaded")
        return model_path

    def detect(self, frame: np.ndarray) -> list[Detection]:
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._detector.detect(mp_image)

        if not result.detections:
            return []

        detections: list[Detection] = []
        for det in result.detections:
            bb = det.bounding_box  # absolute pixel coords
            x = max(0, bb.origin_x)
            y = max(0, bb.origin_y)
            bw = min(bb.width, w - x)
            bh = min(bb.height, h - y)
            score = det.categories[0].score if det.categories else 0.0
            detections.append(Detection(x=x, y=y, w=bw, h=bh, confidence=score))

        return detections

    def close(self) -> None:
        self._detector.close()
