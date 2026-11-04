"""/api/profile: view, edit and delete your own account (FR-018, FR-020).

Viewing and deleting are allowed while suspended or unverified (erasure is
never conditional on account state, NFR-014); editing requires an active,
verified account. Email changes go through Supabase Auth from the frontend,
which confirms the new address (AUTH_DESIGN.md §8.1).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.config.dependencies import enforce_profile_rate_limit, get_auth_service, get_current_user
from app.config.lazy import Provider
from app.domain import User
from app.schemas.error_schema import AUTH_ERROR_RESPONSES
from app.schemas.profile_schema import ProfileResponse, UpdateProfileRequest
from app.service.auth.i_auth_service import IAuthService

router = APIRouter(
    prefix="/api/profile",
    tags=["profile"],
    responses=AUTH_ERROR_RESPONSES,
    dependencies=[Depends(enforce_profile_rate_limit)],
)

CurrentUser = Annotated[User, Depends(get_current_user)]
Auth = Annotated[Provider[IAuthService], Depends(get_auth_service)]


@router.get("", response_model=ProfileResponse)
async def get_profile(user: CurrentUser) -> ProfileResponse:
    return ProfileResponse.from_user(user)


@router.put("", response_model=ProfileResponse)
async def update_profile(body: UpdateProfileRequest, user: CurrentUser, auth: Auth) -> ProfileResponse:
    updated = await auth.get().update_display_name(user, body.display_name)
    return ProfileResponse.from_user(updated)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_account(user: CurrentUser, auth: Auth) -> Response:
    """Permanently deletes the account and all its data (FR-020, NFR-014)."""
    await auth.get().delete_account(user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
