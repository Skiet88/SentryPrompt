"""Dependency providers for FastAPI's Depends(). Tests replace these with
app.dependency_overrides instead of patching modules."""

from functools import lru_cache

from .settings import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()
