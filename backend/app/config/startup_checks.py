"""Development startup check: is the configured LLM model actually offered?

Providers retire models (Groq retired llama-3.1-8b-instant in August 2026);
when that happens every context check fails closed as UNAVAILABLE. This
check says so clearly in the log at startup instead of leaving it to be
discovered from 404s. It never blocks startup.
"""

from __future__ import annotations

import asyncio
import logging
from enum import StrEnum

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.exception import ConfigurationError, ProviderError
from app.llm import LLMConfig, LLMProviderFactory

logger = logging.getLogger(__name__)

CHECK_TIMEOUT_SECONDS = 5.0


class ModelStatus(StrEnum):
    AVAILABLE = "available"
    MISSING = "missing"
    UNVERIFIED = "unverified"
    NOT_CONFIGURED = "not_configured"


async def check_llm_model(
    config: LLMConfig,
    factory: LLMProviderFactory | None = None,
    timeout_seconds: float = CHECK_TIMEOUT_SECONDS,
) -> ModelStatus:
    try:
        provider = (factory or LLMProviderFactory()).create(config)
    except ConfigurationError as exc:
        logger.warning("Screening: LLM provider not usable (%s); context checks will fail", exc)
        return ModelStatus.NOT_CONFIGURED

    label = f"{provider.name} model {provider.model}"
    try:
        available = await asyncio.wait_for(provider.model_is_available(), timeout_seconds)
    except (ProviderError, TimeoutError) as exc:
        logger.warning("Screening: could not verify %s (%s)", label, exc or "timeout")
        return ModelStatus.UNVERIFIED

    if available is None:
        logger.info("Screening: using %s (this provider cannot list its models)", label)
        return ModelStatus.UNVERIFIED
    if not available:
        logger.warning(
            "Screening: %s is NOT offered by the provider; every context check will be "
            "UNAVAILABLE. Set a current model in .env (e.g. GROQ_MODEL).",
            label,
        )
        return ModelStatus.MISSING
    logger.info("Screening: using %s (available)", label)
    return ModelStatus.AVAILABLE


async def check_database(engine: AsyncEngine, timeout_seconds: float = CHECK_TIMEOUT_SECONDS) -> str | None:
    """Log whether the database is reachable and which migration it is on.
    Returns the schema version, or None. Never blocks startup."""

    async def read_version() -> str | None:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT version_num FROM public.alembic_version"))
            return result.scalar_one_or_none()

    try:
        version = await asyncio.wait_for(read_version(), timeout_seconds)
    except (SQLAlchemyError, OSError, TimeoutError) as exc:
        # Exception type only: driver messages can include connection details.
        logger.warning(
            "Database: not reachable or not migrated (%s). Check DATABASE_URL and run "
            "'uv run alembic upgrade head'.",
            type(exc).__name__,
        )
        return None
    logger.info("Database: connected (schema version %s)", version)
    return version
