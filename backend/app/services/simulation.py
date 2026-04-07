from __future__ import annotations

import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.config import settings
from app.db.schemas import Alert, AlertReason, Keypoint, Point2D, StreamPayload, Track
from app.services.logic import FallSignal, avg_velocity, classify_fruin_los, density_per_m2, is_fall, should_override_micro_logic


@dataclass
class PersonState:
    person_id: str
    x: float
    y: float
    vx: float
    vy: float
    spine_angle_deg: float
    bbox_ratio: float
    hold_s: float = 0.0


class StreamSimulator:
    def __init__(self, seed: int = 7) -> None:
        self.rand = random.Random(seed)
        self.camera_id = "cam-main"
        self.zone_id = "zone-exit-a"
        self.people: dict[str, PersonState] = {}
        self.tick = 0
        self._init_people()

    def _init_people(self, count: int = 18) -> None:
        for i in range(count):
            pid = f"Person_{i+1}"
            self.people[pid] = PersonState(
                person_id=pid,
                x=self.rand.uniform(1, 9),
                y=self.rand.uniform(1, 9),
                vx=self.rand.uniform(-0.15, 0.15),
                vy=self.rand.uniform(-0.15, 0.15),
                spine_angle_deg=self.rand.uniform(50, 90),
                bbox_ratio=self.rand.uniform(0.45, 0.9),
            )

    def _update_people(self, dt: float) -> None:
        self.tick += 1
        collapse = 0.25 if (self.tick % 120) > 80 else 1.0

        for person in self.people.values():
            person.x += person.vx * dt * collapse
            person.y += person.vy * dt * collapse
            if person.x < 0.5 or person.x > 9.5:
                person.vx *= -1
            if person.y < 0.5 or person.y > 9.5:
                person.vy *= -1

            person.spine_angle_deg = max(8.0, min(90.0, person.spine_angle_deg + self.rand.uniform(-2.5, 2.5)))
            person.bbox_ratio = max(0.4, min(1.8, person.bbox_ratio + self.rand.uniform(-0.04, 0.05)))

            falling = person.spine_angle_deg < 30.0 and person.bbox_ratio > 1.0
            person.hold_s = person.hold_s + dt if falling else max(0.0, person.hold_s - dt)

        if self.tick % 150 == 0:
            p = self.rand.choice(list(self.people.values()))
            p.spine_angle_deg = self.rand.uniform(10, 22)
            p.bbox_ratio = self.rand.uniform(1.05, 1.5)

    def _make_track(self, p: PersonState) -> Track:
        bbox = [p.x * 50, p.y * 30, p.x * 50 + 28, p.y * 30 + 72]
        keypoints = [
            Keypoint(name="left_shoulder", x=bbox[0] + 8, y=bbox[1] + 18, confidence=0.86),
            Keypoint(name="right_shoulder", x=bbox[0] + 20, y=bbox[1] + 18, confidence=0.88),
            Keypoint(name="left_hip", x=bbox[0] + 10, y=bbox[1] + 45, confidence=0.82),
            Keypoint(name="right_hip", x=bbox[0] + 18, y=bbox[1] + 45, confidence=0.84),
        ]
        return Track(
            person_id=p.person_id,
            bbox=bbox,
            map_point=Point2D(x=round(p.x, 3), y=round(p.y, 3)),
            velocity_mps=round((abs(p.vx) + abs(p.vy)) / 2, 3),
            spine_angle_deg=round(p.spine_angle_deg, 2),
            bbox_ratio=round(p.bbox_ratio, 3),
            keypoints=keypoints,
        )

    def next_payload(self, dt: float) -> StreamPayload:
        self._update_people(dt)
        tracks = [self._make_track(p) for p in self.people.values()]
        people_count = len(tracks)
        density = density_per_m2(people_count, settings.zone_area_m2)
        fruin = classify_fruin_los(density)
        avg_v = avg_velocity([t.velocity_mps for t in tracks])

        alerts: list[Alert] = []

        if should_override_micro_logic(fruin):
            if avg_v < 0.04:
                alerts.append(
                    Alert(
                        event_id=str(uuid.uuid4()),
                        event_type="bottleneck",
                        severity="critical",
                        zone_id=self.zone_id,
                        message=f"LOS {fruin}: velocity collapse detected in {self.zone_id}",
                        reasons=[
                            AlertReason(
                                reason_code="los_override_velocity_drop",
                                details={"fruin_level": fruin, "avg_velocity_mps": avg_v},
                            )
                        ],
                    )
                )
        else:
            for t in tracks:
                signal = FallSignal(
                    person_id=t.person_id,
                    spine_angle_deg=t.spine_angle_deg,
                    bbox_ratio=t.bbox_ratio,
                    hold_seconds=self.people[t.person_id].hold_s,
                )
                if is_fall(signal):
                    alerts.append(
                        Alert(
                            event_id=str(uuid.uuid4()),
                            person_id=t.person_id,
                            event_type="fall",
                            severity="critical",
                            zone_id=self.zone_id,
                            message=(
                                f"{t.person_id}: Spine Angle {t.spine_angle_deg}deg for "
                                f"{round(signal.hold_seconds, 1)}s"
                            ),
                            reasons=[
                                AlertReason(
                                    reason_code="spine_angle_and_aspect_rule",
                                    details={
                                        "spine_angle_deg": t.spine_angle_deg,
                                        "bbox_ratio": t.bbox_ratio,
                                        "hold_seconds": round(signal.hold_seconds, 2),
                                    },
                                )
                            ],
                        )
                    )

        return StreamPayload(
            timestamp=datetime.now(timezone.utc),
            camera_id=self.camera_id,
            zone_id=self.zone_id,
            people_count=people_count,
            density_per_m2=round(density, 4),
            fruin_level=fruin,
            avg_velocity_mps=round(avg_v, 4),
            tracks=tracks,
            alerts=alerts,
        )
