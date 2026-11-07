import pytest

from app.exception import ConfigurationError
from app.llm import LLMProviderFactory

factory = LLMProviderFactory()


def test_gemini_free_tier_refused_in_production(config):
    with pytest.raises(ConfigurationError, match="not allowed in production"):
        factory.create(config.with_(llm_provider="gemini", app_env="production"))


def test_gemini_paid_tier_allowed_in_production(config):
    provider = factory.create(
        config.with_(llm_provider="gemini", app_env="production", gemini_paid_tier=True)
    )
    assert provider.name == "gemini"


def test_gemini_free_tier_allowed_in_development(config):
    assert factory.create(config.with_(llm_provider="gemini")).name == "gemini"


@pytest.mark.parametrize("name", ["groq", "ollama"])
def test_non_training_providers_allowed_in_production(config, name):
    assert factory.create(config.with_(llm_provider=name, app_env="production")).name == name
