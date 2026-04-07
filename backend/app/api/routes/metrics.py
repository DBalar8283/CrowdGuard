from datetime import datetime

from fastapi import APIRouter, Query

from app.db.schemas import MetricsPoint, MetricsResponse
from app.services.event_service import list_metrics

router = APIRouter(prefix="/zones", tags=["metrics"])


@router.get("/{zone_id}/metrics", response_model=MetricsResponse)
def get_zone_metrics(zone_id: str, limit: int = Query(default=120, ge=1, le=1000)) -> MetricsResponse:
    rows = list_metrics(zone_id=zone_id, limit=limit)
    points = [
        MetricsPoint(
            timestamp=datetime.fromisoformat(row["timestamp"]),
            people_count=row["people_count"],
            density_per_m2=row["density_per_m2"],
            avg_velocity_mps=row["avg_velocity_mps"],
            fruin_level=row["fruin_level"],
        )
        for row in rows
    ]
    camera_id = rows[0]["camera_id"] if rows else "cam-main"
    return MetricsResponse(camera_id=camera_id, zone_id=zone_id, points=points)
