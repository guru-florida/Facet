import asyncio
import logging

import cv2
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

from app.config import settings

logger = logging.getLogger(__name__)

# Shared frame — pipeline writes, video WS reads.
# _frame_seq increments each time a new frame arrives; the WS handler uses it
# to skip sends when the pipeline hasn't produced a new frame yet.
_latest_frame: np.ndarray | None = None
_frame_seq: int = 0
_active_clients: int = 0


def set_latest_frame(frame: np.ndarray) -> None:
    """Called from the pipeline thread. GIL protects the int and reference swap."""
    global _latest_frame, _frame_seq
    _latest_frame = frame
    _frame_seq += 1


def get_active_client_count() -> int:
    return _active_clients


async def video_ws_handler(ws: WebSocket) -> None:
    global _active_clients
    await ws.accept()
    _active_clients += 1
    logger.debug("Video WS connected; clients=%d", _active_clients)

    encode_params = [cv2.IMWRITE_JPEG_QUALITY, settings.video_jpeg_quality]
    # Poll at the streaming FPS cap; only encode+send when the frame is new.
    poll_interval = 1.0 / settings.video_fps_cap
    last_sent_seq = -1

    try:
        while True:
            seq = _frame_seq
            if seq != last_sent_seq:
                frame = _latest_frame
                if frame is not None:
                    ret, buf = cv2.imencode(".jpg", frame, encode_params)
                    if ret:
                        await ws.send_bytes(buf.tobytes())
                last_sent_seq = seq
            await asyncio.sleep(poll_interval)
    except WebSocketDisconnect:
        logger.debug("Video WS disconnected")
    except Exception as exc:
        logger.warning("Video WS error: %s", exc)
    finally:
        _active_clients -= 1
        logger.debug("Video WS cleaned up; clients=%d", _active_clients)
