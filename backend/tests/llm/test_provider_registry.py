import pytest

from app.exception import ConfigurationError
from app.llm import ProviderRegistry, provider_registry
from tests.conftest import FakeProvider


def test_built_in_providers_register_themselves():
    assert provider_registry.names() == ["gemini", "groq", "ollama"]


def test_new_provider_added_without_editing_registry(config):
    registry = ProviderRegistry()
    registry.register(FakeProvider)
    assert isinstance(registry.create("fake", config), FakeProvider)


def test_duplicate_registration_rejected():
    registry = ProviderRegistry()
    registry.register(FakeProvider)
    with pytest.raises(ConfigurationError, match="already registered"):
        registry.register(FakeProvider)


def test_unknown_provider_lists_choices(config):
    with pytest.raises(ConfigurationError, match="Choose one of: gemini, groq, ollama"):
        provider_registry.create("openai", config)


def test_name_is_case_and_space_insensitive(config):
    assert provider_registry.create(" Groq ", config).name == "groq"
