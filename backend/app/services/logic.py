from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from app.db.schemas import FruinLevel


LOS_ORDER: list[FruinLevel] = ["A", "B", "C", "D", "E", "F"]


def classify_fruin_los(density_per_m2: float) -> FruinLevel:
    if density_per_m2 < 0.3:
        return "A"
    if density_per_m2 < 0.5:
        return "B"
    if density_per_m2 < 0.8:
        return "C"
    if density_per_m2 < 1.2:
        return "D"
    if density_per_m2 < 1.6:
        return "E"
    return "F"


def density_per_m2(people_count: int, area_m2: float) -> float:
    if area_m2 <= 0:
        raise ValueError("area_m2 must be > 0")
    return people_count / area_m2


@dataclass
class FallSignal:
    person_id: str
    spine_angle_deg: float
    bbox_ratio: float
    hold_seconds: float


def is_fall(signal: FallSignal) -> bool:
    return signal.spine_angle_deg < 30.0 and signal.bbox_ratio > 1.0 and signal.hold_seconds > 5.0


def should_override_micro_logic(fruin_level: FruinLevel) -> bool:
    return fruin_level in {"E", "F"}


def avg_velocity(values: Iterable[float]) -> float:
    values = list(values)
    if not values:
        return 0.0
    return sum(values) / len(values)


def estimate_velocity(prev_point: tuple[float, float], curr_point: tuple[float, float], dt_s: float) -> float:
    if dt_s <= 0:
        return 0.0
    dx = curr_point[0] - prev_point[0]
    dy = curr_point[1] - prev_point[1]
    return math.sqrt(dx * dx + dy * dy) / dt_s
