from __future__ import annotations

import base64
import math
import uuid
from datetime import datetime, timezone

import cv2

from app.core.config import settings
from app.db.schemas import Alert, AlertReason, Point2D, StreamPayload, Track
from app.services.logic import avg_velocity, classify_fruin_los, density_per_m2

try:
    from ultralytics import YOLO  # type: ignore
except Exception:  # pragma: no cover
    YOLO = None


class RealPerceptionStream:
    def __init__(self) -> None:
        self.camera_id = "cam-main"
        self.zone_id = "zone-exit-a"
        self.cap: cv2.VideoCapture | None = None
        self.model = None
        self.hog = None
        self.next_track_idx = 1
        self.prev_tracks: dict[str, tuple[float, float]] = {}

    def start(self) -> None:
        self.cap = self._open_source()
        if not self.cap or not self.cap.isOpened():
            raise RuntimeError("Could not open camera/video source.")

        if settings.detector_mode == "yolo" and YOLO is not None:
            self.model = YOLO(settings.yolo_model)
        else:
            self.hog = cv2.HOGDescriptor()
            self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def stop(self) -> None:
        if self.cap:
            self.cap.release()
            self.cap = None

    def next_payload(self, dt: float) -> StreamPayload | None:
        if not self.cap:
            return None

        ok, frame = self.cap.read()
        if not ok or frame is None:
            return None

        boxes = self._detect_people(frame)
        tracks = self._build_tracks(boxes, frame.shape[1], frame.shape[0], dt)

        people_count = len(tracks)
        density = density_per_m2(people_count, settings.zone_area_m2)
        fruin = classify_fruin_los(density)
        avg_v = avg_velocity([t.velocity_mps for t in tracks])

        alerts: list[Alert] = []
        if fruin in {"E", "F"}:
            alerts.append(
                Alert(
                    event_id=str(uuid.uuid4()),
                    event_type="los_critical",
                    severity="critical",
                    zone_id=self.zone_id,
                    message=f"Critical crowd density detected (LOS {fruin}).",
                    reasons=[
                        AlertReason(
                            reason_code="fruin_density_threshold",
                            details={"fruin_level": fruin, "density_per_m2": round(density, 4)},
                        )
                    ],
                )
            )

        annotated = self._annotate_frame(frame.copy(), tracks, fruin)
        encoded = self._encode_frame(annotated)

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
            frame_jpeg=encoded,
            frame_width=int(frame.shape[1]),
            frame_height=int(frame.shape[0]),
        )

    def _open_source(self) -> cv2.VideoCapture:
        mode = settings.source_mode.lower().strip()
        if mode == "webcam":
            return cv2.VideoCapture(settings.source_camera_index)
        if mode in {"video_file", "rtsp"} and settings.source_uri:
            return cv2.VideoCapture(settings.source_uri)
        raise RuntimeError(
            "Invalid source mode for real feed. Use CROWDGUARD_SOURCE_MODE=webcam|video_file|rtsp"
        )

    def _detect_people(self, frame) -> list[tuple[int, int, int, int]]:
        if self.model is not None:
            results = self.model(frame, verbose=False)
            boxes: list[tuple[int, int, int, int]] = []
            for result in results:
                if result.boxes is None:
                    continue
                xyxy = result.boxes.xyxy.cpu().numpy()
                confs = result.boxes.conf.cpu().numpy()
                classes = result.boxes.cls.cpu().numpy().astype(int)
                for i, cls_id in enumerate(classes):
                    if cls_id != 0:
                        continue
                    if float(confs[i]) < settings.min_detection_conf:
                        continue
                    x1, y1, x2, y2 = xyxy[i]
                    boxes.append((int(x1), int(y1), int(x2), int(y2)))
            return boxes

        rects, _ = self.hog.detectMultiScale(frame, winStride=(8, 8), padding=(8, 8), scale=1.05)
        boxes = []
        for x, y, w, h in rects:
            boxes.append((int(x), int(y), int(x + w), int(y + h)))
        return boxes

    def _build_tracks(self, boxes: list[tuple[int, int, int, int]], frame_w: int, frame_h: int, dt: float) -> list[Track]:
        centers = [((x1 + x2) / 2.0, (y1 + y2) / 2.0) for (x1, y1, x2, y2) in boxes]
        assigned: dict[int, str] = {}
        used_ids: set[str] = set()

        for idx, center in enumerate(centers):
            best_id = None
            best_dist = 999999.0
            for person_id, prev_center in self.prev_tracks.items():
                if person_id in used_ids:
                    continue
                d = math.dist(center, prev_center)
                if d < best_dist and d < 90.0:
                    best_dist = d
                    best_id = person_id

            if best_id is None:
                best_id = f"Person_{self.next_track_idx}"
                self.next_track_idx += 1

            assigned[idx] = best_id
            used_ids.add(best_id)

        tracks: list[Track] = []
        new_prev: dict[str, tuple[float, float]] = {}

        for idx, (x1, y1, x2, y2) in enumerate(boxes):
            person_id = assigned[idx]
            cx, cy = centers[idx]
            prev = self.prev_tracks.get(person_id, (cx, cy))
            px_dist = math.dist((cx, cy), prev)
            velocity_mps = (px_dist / max(dt, 1e-5)) * 0.01
            bbox_h = max((y2 - y1), 1)
            bbox_w = max((x2 - x1), 1)

            tracks.append(
                Track(
                    person_id=person_id,
                    bbox=[float(x1), float(y1), float(x2), float(y2)],
                    map_point=Point2D(x=round((cx / frame_w) * 10, 3), y=round((cy / frame_h) * 10, 3)),
                    velocity_mps=round(velocity_mps, 3),
                    spine_angle_deg=90.0,
                    bbox_ratio=round(bbox_w / bbox_h, 3),
                )
            )
            new_prev[person_id] = (cx, cy)

        self.prev_tracks = new_prev
        return tracks

    def _annotate_frame(self, frame, tracks: list[Track], fruin_level: str):
        box_color = (88, 196, 255)
        if fruin_level in {"E", "F"}:
            box_color = (64, 64, 255)

        for track in tracks:
            x1, y1, x2, y2 = [int(v) for v in track.bbox]
            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
            cv2.putText(
                frame,
                track.person_id,
                (x1, max(14, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                box_color,
                1,
                cv2.LINE_AA,
            )

        cv2.putText(
            frame,
            f"CROWDGUARD DEMO - LOS {fruin_level}",
            (12, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        return frame

    def _encode_frame(self, frame) -> str | None:
        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), settings.frame_quality])
        if not ok:
            return None
        return base64.b64encode(buf.tobytes()).decode("ascii")
