import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter

from app.db.database import get_connection
from app.db.schemas import CalibrationCreateRequest

router = APIRouter(prefix="/calibration", tags=["calibration"])


@router.post("/{camera_id}")
def create_calibration(camera_id: str, body: CalibrationCreateRequest) -> dict:
    calibration_id = str(uuid.uuid4())
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO calibration_profile (id, camera_id, matrix_json, points_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                calibration_id,
                camera_id,
                json.dumps(body.matrix),
                json.dumps([p.model_dump() for p in body.points]),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return {"id": calibration_id, "camera_id": camera_id, "status": "saved"}
