"""POST /api/prompts/screen: screen one prompt (FR-001 to FR-006).

TEMPORARY: served only outside production until login exists (agreed
exception, Settings.unauthenticated_screening_enabled); step 6 adds the
verified-login requirement.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.config.dependencies import enforce_screening_rate_limit, get_screening_service
from app.config.lazy import Provider
from app.schemas.screening_schema import ScreenPromptRequest, ScreenPromptResponse
from app.service.screening.i_screening_service import IScreeningService

router = APIRouter(prefix="/api/prompts", tags=["screening"])


@router.post(
    "/screen",
    response_model=ScreenPromptResponse,
    dependencies=[Depends(enforce_screening_rate_limit)],
)
async def screen_prompt(
    body: ScreenPromptRequest,
    service: Annotated[Provider[IScreeningService], Depends(get_screening_service)],
) -> ScreenPromptResponse:
    outcome = await service.get().screen(body.text, body.channel)
    return ScreenPromptResponse.from_outcome(outcome)
