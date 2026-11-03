"""Application entry point. Builds the FastAPI app and wires its dependencies.

Run locally with:  uv run fastapi dev app/main.py
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import health_router
from app.config.dependencies import get_settings
from app.config.logging_config import configure_logging
from app.config.request_size_limit import RequestSizeLimitMiddleware
from app.config.security_headers import SecurityHeadersMiddleware
from app.config.settings import Settings
from app.exception.handlers import register_exception_handlers

DOCS_PATHS = ("/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory. Passing settings (e.g. in tests) overrides the
    values read from the environment for every request."""
    overridden = settings is not None
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    docs = settings.docs_enabled
    app = FastAPI(
        title="SentryPrompt4 API",
        version=__version__,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )
    if overridden:
        app.dependency_overrides[get_settings] = lambda: settings

    # Added inner-first: the last middleware added runs first on each request.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=settings.max_request_bytes)
    app.add_middleware(
        SecurityHeadersMiddleware,
        enable_hsts=settings.is_production,
        csp_exempt_paths=DOCS_PATHS if docs else (),
    )

    register_exception_handlers(app)
    app.include_router(health_router.router)
    return app


app = create_app()
