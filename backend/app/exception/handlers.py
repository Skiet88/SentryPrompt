"""Translates application exceptions into HTTP responses in one place."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .app_exceptions import SentryPromptError


async def _handle_app_error(_: Request, exc: SentryPromptError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "message": str(exc)},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(SentryPromptError, _handle_app_error)
