from fastapi import APIRouter

from app.api.routes.calibration import router as calibration_router
from app.api.routes.events import router as events_router
from app.api.routes.health import router as health_router
from app.api.routes.metrics import router as metrics_router

api_router = APIRouter(prefix="/v1")
api_router.include_router(health_router)
api_router.include_router(events_router)
api_router.include_router(calibration_router)
api_router.include_router(metrics_router)
