"""Application entry point. Builds the FastAPI app and wires its dependencies.

Run locally with:  uv run fastapi dev app/main.py
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import health_router, screening_router
from app.config.composition import build_screening_service
from app.config.database import create_database_engine
from app.config.dependencies import get_settings
from app.config.lazy import Lazy
from app.config.logging_config import configure_logging
from app.config.rate_limiter import RateLimitPolicy, SlidingWindowRateLimiter
from app.config.request_size_limit import RequestSizeLimitMiddleware
from app.config.security_headers import SecurityHeadersMiddleware
from app.config.settings import Settings
from app.config.startup_checks import check_database, check_llm_model
from app.exception.handlers import register_exception_handlers
from app.repository.memory.screening_records import InMemoryScreeningRecordWriter
from app.repository.postgres.screening_records import PostgresScreeningRecordWriter
from app.repository.screening_record_writer import ScreeningRecordWriter

logger = logging.getLogger(__name__)

DOCS_PATHS = ("/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory. Passing settings (e.g. in tests) overrides the
    values read from the environment for every request."""
    overridden = settings is not None
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    resolved_settings = settings

    @asynccontextmanager
    async def lifespan(app_: FastAPI) -> AsyncIterator[None]:
        engine = app_.state.database_engine
        if not resolved_settings.is_production:
            await check_llm_model(resolved_settings)
            if engine is not None:
                await check_database(engine)
        yield
        if engine is not None:
            await engine.dispose()

    docs = settings.docs_enabled
    app = FastAPI(
        lifespan=lifespan,
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
    _wire_screening(app, settings)
    app.include_router(health_router.router)
    if settings.unauthenticated_screening_enabled:
        app.include_router(screening_router.router)
    return app


def _wire_screening(app: FastAPI, settings: Settings) -> None:
    """Dependency injection for the screening endpoint. The service is built
    on first use, so the app (and /health) starts without an LLM key."""
    records = _screening_records(app, settings)
    app.state.screening_records = records
    app.state.screening_service = Lazy(lambda: build_screening_service(settings, records=records))
    window = settings.rate_limit_window_seconds
    app.state.screening_rate_limits = RateLimitPolicy(
        per_client=SlidingWindowRateLimiter(settings.screening_rate_limit_per_client, window),
        global_limit=SlidingWindowRateLimiter(settings.screening_rate_limit_global, window),
    )


def _screening_records(app: FastAPI, settings: Settings) -> ScreeningRecordWriter:
    """PostgreSQL when DATABASE_URL is set (required in production); otherwise
    in memory, which development may use without a database."""
    if settings.database_url is None:
        app.state.database_engine = None
        logger.warning("No DATABASE_URL: screening records are kept in memory only (development)")
        return InMemoryScreeningRecordWriter()
    engine = create_database_engine(settings)
    app.state.database_engine = engine
    return PostgresScreeningRecordWriter(engine)


app = create_app()
