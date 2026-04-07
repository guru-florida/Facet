from __future__ import annotations
import logging
import os

import cv2
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class FaceRecognizer:
    """ArcFace embedding extraction + cosine similarity matching (Stage B).

    Downloads and uses the buffalo_sc w600k_mbf.onnx model from insightface directly
    via onnxruntime.  We bypass FaceAnalysis.get() because that re-runs face detection
    on the crop — which fails on tight face crops with no background context.

    The model takes a (1, 3, 112, 112) BGR float32 tensor normalised to [-1, 1]
    and returns a (1, 512) embedding.
    """

    _MODEL_SUBPATH = "models/buffalo_sc/w600k_mbf.onnx"

    def __init__(self) -> None:
        self._session: object | None = None
        self._input_name: str = ""
        self._ready = False

    def load(self) -> None:
        """Load the ArcFace onnx model.  Downloads buffalo_sc via insightface if needed."""
        os.environ["INSIGHTFACE_HOME"] = settings.insightface_home
        os.makedirs(settings.insightface_home, exist_ok=True)

        model_path = os.path.join(settings.insightface_home, self._MODEL_SUBPATH)

        if not os.path.exists(model_path):
            # Model not on disk yet — try to download via insightface.
            # This can fail on some macOS environments due to ml_dtypes version
            # conflicts; if so, log clearly and bail.
            try:
                import insightface
                app = insightface.app.FaceAnalysis(
                    name="buffalo_sc",
                    root=settings.insightface_home,
                    providers=["CPUExecutionProvider"],
                )
                app.prepare(ctx_id=-1, det_size=(640, 640))
                logger.info("insightface buffalo_sc models downloaded/verified")
            except Exception as exc:
                logger.error(
                    "insightface download failed and model not found at %s: %s — "
                    "run: python -c \"import insightface; "
                    "insightface.app.FaceAnalysis('buffalo_sc').prepare(ctx_id=-1)\"",
                    model_path,
                    exc,
                )
                return
        else:
            logger.info("ArcFace model found at %s — skipping insightface download", model_path)

        if not os.path.exists(model_path):
            logger.error("ArcFace model still not found at %s after download attempt", model_path)
            return

        try:
            import onnxruntime as ort
            sess = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
            self._session = sess
            self._input_name = sess.get_inputs()[0].name
            self._ready = True
            logger.info("ArcFace recognition model loaded from %s", model_path)
        except Exception as exc:
            logger.error("Failed to load ArcFace onnx model: %s", exc)

    @property
    def ready(self) -> bool:
        return self._ready

    def get_embedding(self, face_crop: np.ndarray) -> np.ndarray | None:
        """Extract a 512-d ArcFace embedding from a face crop (any size, BGR).

        Returns a unit-normalised embedding, or None on failure.
        """
        if not self._ready or self._session is None:
            return None
        try:
            img = cv2.resize(face_crop, (112, 112))
            # (H, W, C) → (1, C, H, W), normalise BGR to [-1, 1]
            blob = img.transpose(2, 0, 1)[np.newaxis].astype(np.float32)
            blob = (blob - 127.5) / 127.5
            output = self._session.run(None, {self._input_name: blob})
            emb = output[0].flatten()
            norm = np.linalg.norm(emb)
            if norm == 0:
                return None
            return emb / norm
        except Exception as exc:
            logger.debug("Embedding extraction failed: %s", exc)
            return None

    @staticmethod
    def match(
        embedding: np.ndarray,
        known_embeddings: dict[str, list[np.ndarray]],
        threshold: float | None = None,
    ) -> tuple[str | None, float]:
        """Cosine similarity match against all known identity embeddings.

        Returns (identity_id, score) where identity_id is None if no match
        exceeds the threshold.
        """
        if threshold is None:
            threshold = settings.recognition_threshold

        best_id: str | None = None
        best_score: float = -1.0

        for identity_id, samples in known_embeddings.items():
            for sample in samples:
                score = float(np.dot(embedding, sample))
                if score > best_score:
                    best_score = score
                    best_id = identity_id

        if best_score < threshold:
            return None, best_score
        return best_id, best_score
