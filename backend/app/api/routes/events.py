from datetime import datetime

from fastapi import APIRouter, Query

from app.db.schemas import EventRecord
from app.services.event_service import list_events

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventRecord])
def get_events(limit: int = Query(default=100, ge=1, le=500)) -> list[EventRecord]:
    rows = list_events(limit=limit)
    return [
        EventRecord(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            camera_id=row["camera_id"],
            zone_id=row["zone_id"],
            event_type=row["event_type"],
            severity=row["severity"],
            fruin_level=row["fruin_level"],
            message=row["message"],
        )
        for row in rows
    ]
