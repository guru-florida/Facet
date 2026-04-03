import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

from app.models.track import Track

logger = logging.getLogger(__name__)


class PresenceConnectionManager:
    """Manages active WebSocket connections for presence events."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []
        self._event_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def publish_from_thread(self, event: dict[str, Any]) -> None:
        """Thread-safe: schedule an event broadcast from a non-async thread."""
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._event_queue.put_nowait, event)

    async def connect(self, ws: WebSocket, snapshot: list[Track]) -> None:
        """Accept connection and immediately send current state snapshot."""
        await ws.accept()
        # Send snapshot before adding to connections so the broadcast loop
        # cannot race with us and produce duplicate/out-of-order events.
        try:
            payload = json.dumps({
                "type": "snapshot",
                "tracks": [t.model_dump() for t in snapshot],
            })
            await ws.send_text(payload)
        except Exception as exc:
            logger.warning("Failed to send snapshot to new client: %s", exc)
            return
        self._connections.append(ws)
        logger.debug("Presence WS connected; total=%d", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        try:
            self._connections.remove(ws)
        except ValueError:
            pass  # already removed by broadcast_loop dead-socket cleanup
        logger.debug("Presence WS disconnected; total=%d", len(self._connections))

    async def broadcast_loop(self) -> None:
        """Drains the event queue and broadcasts to all live connections."""
        while True:
            event = await self._event_queue.get()
            try:
                payload = json.dumps(event)
            except Exception as exc:
                logger.error("Failed to serialise presence event: %s", exc)
                continue
            dead: list[WebSocket] = []
            for ws in list(self._connections):
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                try:
                    self._connections.remove(ws)
                except ValueError:
                    pass


presence_manager = PresenceConnectionManager()
