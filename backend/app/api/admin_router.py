"""/api/admin: account administration (FR-021, FR-022).

Every route requires an active, verified administrator (role from our
database only). Account-level only: there is no route here, or anywhere,
that lets an admin reach conversations or messages (NFR-013).
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query

from app.config.dependencies import enforce_admin_rate_limit, get_admin_service, get_admin_user
from app.config.lazy import Provider
from app.domain import User
from app.schemas.admin_schema import (
    AdminUserResponse,
    AuditLogEntryResponse,
    StatusChangeRequest,
    StatusChangeResponse,
)
from app.schemas.error_schema import AUTH_ERROR_RESPONSES, ErrorResponse
from app.service.admin.admin_service import MAX_PAGE_SIZE
from app.service.admin.i_admin_service import IAdminService

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    responses={**AUTH_ERROR_RESPONSES, 404: {"model": ErrorResponse, "description": "No such account"}},
    dependencies=[Depends(enforce_admin_rate_limit)],
)

AdminUser = Annotated[User, Depends(get_admin_user)]
Admin = Annotated[Provider[IAdminService], Depends(get_admin_service)]
OptionalReason = Annotated[StatusChangeRequest | None, Body()]


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    admin: AdminUser,
    service: Admin,
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    per_page: Annotated[int, Query(alias="perPage", ge=1, le=MAX_PAGE_SIZE)] = 50,
) -> list[AdminUserResponse]:
    return [AdminUserResponse.from_view(v) for v in await service.get().list_users(admin, page, per_page)]


@router.post("/users/{user_id}/suspend", response_model=StatusChangeResponse)
async def suspend_user(
    user_id: UUID, admin: AdminUser, service: Admin, body: OptionalReason = None
) -> StatusChangeResponse:
    reason = body.reason if body else ""
    return StatusChangeResponse.from_result(await service.get().suspend(admin, str(user_id), reason))


@router.post("/users/{user_id}/reinstate", response_model=StatusChangeResponse)
async def reinstate_user(
    user_id: UUID, admin: AdminUser, service: Admin, body: OptionalReason = None
) -> StatusChangeResponse:
    reason = body.reason if body else ""
    return StatusChangeResponse.from_result(await service.get().reinstate(admin, str(user_id), reason))


@router.get("/audit-log", response_model=list[AuditLogEntryResponse])
async def audit_log(
    admin: AdminUser,
    service: Admin,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 50,
    offset: Annotated[int, Query(ge=0, le=1_000_000)] = 0,
) -> list[AuditLogEntryResponse]:
    return [AuditLogEntryResponse.from_entry(e) for e in await service.get().audit_log(admin, limit, offset)]
