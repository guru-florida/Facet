"""Presence Service — FastAPI application entry point."""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.pipeline.camera import CameraCapture
from app.pipeline.pipeline import PresencePipeline
from app.pipeline.recognizer import FaceRecognizer
from app.store.db import init_db
from app.store.identity_repo import IdentityRepo
from app.store.track_store import TrackStore
from app.ws.presence_ws import presence_manager
from app.ws.video_ws import video_ws_handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("Starting Presence Service")

    # Storage
    init_db()
    identity_repo = IdentityRepo()
    identity_repo.load_cache()

    # Camera
    camera = CameraCapture()
    camera.start()

    # Track store
    track_store = TrackStore()

    # Recognizer (loads insightface models — may take a few seconds)
    recognizer = FaceRecognizer()
    recognizer.load()

    # Presence WebSocket manager — capture the running loop
    loop = asyncio.get_event_loop()
    presence_manager.set_loop(loop)

    # Start broadcast task
    broadcast_task = asyncio.create_task(presence_manager.broadcast_loop())

    # Pipeline
    pipeline = PresencePipeline(
        camera=camera,
        track_store=track_store,
        identity_repo=identity_repo,
        recognizer=recognizer,
        presence_publish_fn=presence_manager.publish_from_thread,
    )
    pipeline.start()

    # Stash on app.state for dependency injection
    app.state.track_store = track_store
    app.state.identity_repo = identity_repo
    app.state.pipeline = pipeline
    app.state.recognizer = recognizer

    logger.info("Presence Service ready")
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("Shutting down Presence Service")
    pipeline.stop()
    camera.stop()
    broadcast_task.cancel()
    try:
        await broadcast_task
    except asyncio.CancelledError:
        pass
    logger.info("Shutdown complete")


app = FastAPI(title="Presence Service", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── REST routers ──────────────────────────────────────────────────────────────
from app.api import presence, identities, status  # noqa: E402

app.include_router(presence.router, prefix="/api")
app.include_router(identities.router, prefix="/api")
app.include_router(status.router, prefix="/api")


# ── WebSocket endpoints ───────────────────────────────────────────────────────
@app.websocket("/ws/video")
async def ws_video(ws: WebSocket) -> None:
    await video_ws_handler(ws)


@app.websocket("/ws/presence")
async def ws_presence(ws: WebSocket) -> None:
    track_store: TrackStore = ws.app.state.track_store
    await presence_manager.connect(ws, snapshot=track_store.get_all())
    try:
        while True:
            # Send a ping every 25 s to keep the Vite dev-proxy (and nginx in
            # production) from closing the idle connection.
            await asyncio.sleep(25)
            await ws.send_text('{"type":"ping"}')
    except Exception:
        pass
    finally:
        presence_manager.disconnect(ws)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# ── Static file serving (single-container deployment) ────────────────────────
# Mount LAST so API/WS routes always take priority.
# In dev (no ./static dir) this block is simply skipped.
_static_dir = os.environ.get("STATIC_DIR", "static")
if os.path.isdir(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="frontend")
