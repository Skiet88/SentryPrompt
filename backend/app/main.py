"""Application entry point. Builds the FastAPI app and wires its dependencies.

Run locally with:  uv run fastapi dev app/main.py
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import health_router
from app.config.dependencies import get_settings
from app.config.settings import Settings
from app.exception.handlers import register_exception_handlers


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory. Passing settings (e.g. in tests) overrides the
    values read from the environment for every request."""
    app = FastAPI(title="SentryPrompt4 API", version=__version__)
    if settings is None:
        settings = get_settings()
    else:
        app.dependency_overrides[get_settings] = lambda: settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(health_router.router)
    return app


app = create_app()
