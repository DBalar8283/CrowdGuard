from __future__ import annotations

import json

from app.db.database import get_connection
from app.db.schemas import StreamPayload


def persist_payload(payload: StreamPayload) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO metric_timeseries (timestamp, camera_id, zone_id, people_count, density_per_m2, avg_velocity_mps, fruin_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.timestamp.isoformat(),
                payload.camera_id,
                payload.zone_id,
                payload.people_count,
                payload.density_per_m2,
                payload.avg_velocity_mps,
                payload.fruin_level,
            ),
        )

        for alert in payload.alerts:
            conn.execute(
                """
                INSERT INTO event (id, timestamp, camera_id, zone_id, event_type, severity, fruin_level, message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert.event_id,
                    payload.timestamp.isoformat(),
                    payload.camera_id,
                    payload.zone_id,
                    alert.event_type,
                    alert.severity,
                    payload.fruin_level,
                    alert.message,
                ),
            )
            for reason in alert.reasons:
                conn.execute(
                    """
                    INSERT INTO event_reason (event_id, reason_code, evidence_json)
                    VALUES (?, ?, ?)
                    """,
                    (alert.event_id, reason.reason_code, json.dumps(reason.details)),
                )

        conn.commit()
    finally:
        conn.close()


def list_events(limit: int = 100) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, timestamp, camera_id, zone_id, event_type, severity, fruin_level, message
            FROM event
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def list_metrics(zone_id: str, limit: int = 120) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT timestamp, people_count, density_per_m2, avg_velocity_mps, fruin_level, camera_id, zone_id
            FROM metric_timeseries
            WHERE zone_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (zone_id, limit),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]
    finally:
        conn.close()
