from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Camera
    camera_index: int = 0

    # Storage
    db_path: str = "./data/presence.db"
    insightface_home: str = "./data/insightface_models"

    # Pipeline thresholds
    detection_confidence: float = 0.6
    recognition_confidence: float = 0.7
    recognition_threshold: float = 0.4
    recognition_interval: float = 1.0
    stability_frames: int = 8
    leave_debounce_seconds: float = 5.0
    min_face_px: int = 80

    # Pipeline frame rate
    pipeline_fps_idle: int = 5        # no video WS clients connected
    pipeline_fps_streaming: int = 30  # ≥1 video WS client connected

    # Video stream
    video_fps_cap: int = 30
    video_jpeg_quality: int = 70

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000


settings = Settings()
