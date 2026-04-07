from fastapi import APIRouter

from app.core.config import settings
from app.db.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(app=settings.app_name, version=settings.app_version)
