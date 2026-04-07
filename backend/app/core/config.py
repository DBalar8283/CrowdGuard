from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CrowdGuard API"
    app_version: str = "0.1.0"
    env: str = "dev"
    database_path: str = "backend/crowdguard.db"
    stream_hz: int = 10
    zone_area_m2: float = 100.0
    los_override_threshold: str = "E"

    source_mode: str = "simulation"  # simulation | webcam | video_file | rtsp
    source_uri: str = ""
    source_camera_index: int = 0

    detector_mode: str = "yolo"  # yolo | hog
    yolo_model: str = "yolov8n.pt"
    min_detection_conf: float = 0.35
    frame_quality: int = 72

    model_config = SettingsConfigDict(env_prefix="CROWDGUARD_", extra="ignore")


settings = Settings()
