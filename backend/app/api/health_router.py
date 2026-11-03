from typing import Annotated

from fastapi import APIRouter, Depends

from app import __version__
from app.config.dependencies import get_settings
from app.config.settings import Settings
from app.schemas.health_schema import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    """Liveness check. Makes no external calls, so it stays fast and reliable."""
    return HealthResponse(status="ok", version=__version__, environment=settings.app_env)
