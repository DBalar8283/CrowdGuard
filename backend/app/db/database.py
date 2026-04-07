import sqlite3
from pathlib import Path

from app.core.config import settings


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS camera (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source_uri TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS zone (
    id TEXT PRIMARY KEY,
    camera_id TEXT NOT NULL,
    name TEXT NOT NULL,
    area_m2 REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(camera_id) REFERENCES camera(id)
);

CREATE TABLE IF NOT EXISTS calibration_profile (
    id TEXT PRIMARY KEY,
    camera_id TEXT NOT NULL,
    matrix_json TEXT NOT NULL,
    points_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(camera_id) REFERENCES camera(id)
);

CREATE TABLE IF NOT EXISTS event (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    camera_id TEXT NOT NULL,
    zone_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    fruin_level TEXT NOT NULL,
    message TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS event_reason (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    FOREIGN KEY(event_id) REFERENCES event(id)
);

CREATE TABLE IF NOT EXISTS metric_timeseries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    camera_id TEXT NOT NULL,
    zone_id TEXT NOT NULL,
    people_count INTEGER NOT NULL,
    density_per_m2 REAL NOT NULL,
    avg_velocity_mps REAL NOT NULL,
    fruin_level TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_event_timestamp ON event(timestamp);
CREATE INDEX IF NOT EXISTS idx_event_zone ON event(zone_id);
CREATE INDEX IF NOT EXISTS idx_event_severity ON event(severity);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metric_timeseries(timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_zone ON metric_timeseries(zone_id);
"""


def _ensure_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    _ensure_parent(settings.database_path)
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()
