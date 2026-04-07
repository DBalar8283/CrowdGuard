from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


FruinLevel = Literal["A", "B", "C", "D", "E", "F"]
Severity = Literal["info", "warn", "critical"]


class Point2D(BaseModel):
    x: float
    y: float


class Keypoint(BaseModel):
    name: str
    x: float
    y: float
    confidence: float = Field(ge=0, le=1)


class Track(BaseModel):
    person_id: str
    bbox: list[float] = Field(description="[x1, y1, x2, y2]")
    map_point: Point2D
    velocity_mps: float
    spine_angle_deg: float
    bbox_ratio: float
    keypoints: list[Keypoint] = Field(default_factory=list)


class AlertReason(BaseModel):
    reason_code: str
    details: dict


class Alert(BaseModel):
    event_id: str
    person_id: str | None = None
    event_type: Literal["fall", "los_critical", "bottleneck"]
    severity: Severity
    zone_id: str
    message: str
    reasons: list[AlertReason]


class StreamPayload(BaseModel):
    version: Literal["v1"] = "v1"
    timestamp: datetime
    camera_id: str
    zone_id: str
    people_count: int
    density_per_m2: float
    fruin_level: FruinLevel
    avg_velocity_mps: float
    tracks: list[Track]
    alerts: list[Alert]
    frame_jpeg: str | None = None
    frame_width: int | None = None
    frame_height: int | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    app: str
    version: str


class EventRecord(BaseModel):
    id: str
    timestamp: datetime
    camera_id: str
    zone_id: str
    event_type: str
    severity: Severity
    fruin_level: FruinLevel
    message: str


class CalibrationCreateRequest(BaseModel):
    camera_id: str
    points: list[Point2D] = Field(min_length=4)
    matrix: list[list[float]] = Field(min_length=3, max_length=3)


class MetricsPoint(BaseModel):
    timestamp: datetime
    people_count: int
    density_per_m2: float
    avg_velocity_mps: float
    fruin_level: FruinLevel


class MetricsResponse(BaseModel):
    camera_id: str
    zone_id: str
    points: list[MetricsPoint]
