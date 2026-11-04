"""Translates exceptions into HTTP responses in one place.

Client errors (4xx) return our own message. Server errors (5xx) and
unexpected exceptions return a generic message; details go only to the
server log (SECURITY_RULES.md §4).
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.error_schema import ErrorResponse, FieldProblem, ValidationErrorResponse

from .app_exceptions import AuthenticationError, RateLimitExceededError, SentryPromptError

logger = logging.getLogger(__name__)

GENERIC_SERVER_ERROR = "The server could not complete the request."


def _error_response(
    status_code: int, error_code: str, message: str, headers: dict[str, str] | None = None
) -> JSONResponse:
    body = ErrorResponse(error=error_code, message=message)
    return JSONResponse(status_code=status_code, content=body.model_dump(), headers=headers)


async def _handle_app_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, SentryPromptError):
        return await _handle_unexpected_error(request, exc)
    if exc.status_code >= 500:
        logger.error("%s: %s", exc.error_code, exc)
        return _error_response(exc.status_code, exc.error_code, GENERIC_SERVER_ERROR)
    headers = None
    if isinstance(exc, RateLimitExceededError):
        headers = {"Retry-After": str(exc.retry_after_seconds)}
    elif isinstance(exc, AuthenticationError):
        headers = {"WWW-Authenticate": "Bearer"}
    return _error_response(exc.status_code, exc.error_code, str(exc), headers)


async def _handle_validation_error(_: Request, exc: Exception) -> JSONResponse:
    """FastAPI's default 422 echoes the submitted values back. Prompts may
    contain personal data, so only the field and the problem are returned."""
    errors = exc.errors() if isinstance(exc, RequestValidationError) else []
    body = ValidationErrorResponse(
        error="invalid_request",
        message="The request is not valid.",
        details=[
            FieldProblem(
                field=".".join(str(part) for part in error.get("loc", ()) if part != "body"),
                problem=str(error.get("msg", "")),
            )
            for error in errors
        ],
    )
    return JSONResponse(status_code=422, content=body.model_dump())


async def _handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", type(exc).__name__)
    return _error_response(500, "internal_error", GENERIC_SERVER_ERROR)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(SentryPromptError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)
