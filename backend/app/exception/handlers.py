"""Translates exceptions into HTTP responses in one place.

Client errors (4xx) return our own message. Server errors (5xx) and
unexpected exceptions return a generic message; details go only to the
server log (SECURITY_RULES.md §4).
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .app_exceptions import SentryPromptError

logger = logging.getLogger(__name__)

GENERIC_SERVER_ERROR = "The server could not complete the request."


def _error_response(status_code: int, error_code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": error_code, "message": message})


async def _handle_app_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, SentryPromptError):
        return await _handle_unexpected_error(request, exc)
    if exc.status_code >= 500:
        logger.error("%s: %s", exc.error_code, exc)
        return _error_response(exc.status_code, exc.error_code, GENERIC_SERVER_ERROR)
    return _error_response(exc.status_code, exc.error_code, str(exc))


async def _handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", type(exc).__name__)
    return _error_response(500, "internal_error", GENERIC_SERVER_ERROR)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(SentryPromptError, _handle_app_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)
