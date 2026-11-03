import pytest

from app.exception import ConfigurationError
from app.llm import LLMProviderFactory
from app.llm.providers.gemini_provider import GeminiProvider
from app.llm.providers.groq_provider import GroqProvider
from app.llm.providers.ollama_provider import OllamaProvider

factory = LLMProviderFactory()


def test_default_provider_is_groq(config):
    assert isinstance(factory.create(config), GroqProvider)


@pytest.mark.parametrize("name, cls", [
    ("groq", GroqProvider), ("gemini", GeminiProvider), ("ollama", OllamaProvider),
])
def test_provider_selected_by_setting(config, name, cls):
    assert isinstance(factory.create(config.with_(llm_provider=name)), cls)


def test_explicit_name_overrides_setting(config):
    assert isinstance(factory.create(config, name="gemini"), GeminiProvider)


def test_model_is_configurable(config):
    provider = factory.create(config.with_(groq_model="llama-3.3-70b-versatile"))
    assert provider.model == "llama-3.3-70b-versatile"


@pytest.mark.parametrize("name, key_field", [("groq", "groq_api_key"), ("gemini", "gemini_api_key")])
def test_missing_api_key_rejected(config, name, key_field):
    with pytest.raises(ConfigurationError, match=key_field.upper()):
        factory.create(config.with_(llm_provider=name, **{key_field: ""}))
