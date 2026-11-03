import json

import pytest

from app.llm import ProviderError, get_provider
from app.llm.base import parse_classification
from app.llm.gemini_provider import GeminiProvider
from app.llm.groq_provider import GroqProvider
from app.llm.ollama_provider import OllamaProvider
from app.screening.redaction import redact


# ---- Provider selection --------------------------------------------------

def test_default_provider_is_groq():
    assert isinstance(get_provider(env={"GROQ_API_KEY": "k"}), GroqProvider)


@pytest.mark.parametrize("name, cls", [
    ("groq", GroqProvider), ("gemini", GeminiProvider), ("ollama", OllamaProvider),
])
def test_provider_selected_by_setting(name, cls):
    env = {"LLM_PROVIDER": name, "GROQ_API_KEY": "k", "GEMINI_API_KEY": "k"}
    assert isinstance(get_provider(env=env), cls)


def test_explicit_name_overrides_setting():
    env = {"LLM_PROVIDER": "groq", "GEMINI_API_KEY": "k"}
    assert isinstance(get_provider("gemini", env=env), GeminiProvider)


def test_model_is_configurable():
    provider = get_provider(env={"GROQ_API_KEY": "k", "GROQ_MODEL": "llama-3.3-70b-versatile"})
    assert provider.model == "llama-3.3-70b-versatile"


def test_unknown_provider_rejected():
    with pytest.raises(ProviderError, match="Unknown"):
        get_provider("openai", env={})


def test_missing_api_key_rejected():
    with pytest.raises(ProviderError, match="GROQ_API_KEY"):
        get_provider("groq", env={})


# ---- Privacy guard ---------------------------------------------------------

def test_gemini_free_tier_refused_in_production():
    env = {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "k", "APP_ENV": "production"}
    with pytest.raises(ProviderError, match="not allowed in production"):
        get_provider(env=env)


def test_gemini_paid_tier_allowed_in_production():
    env = {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "k",
           "APP_ENV": "production", "GEMINI_PAID_TIER": "true"}
    assert isinstance(get_provider(env=env), GeminiProvider)


def test_gemini_free_tier_allowed_in_development():
    assert isinstance(get_provider("gemini", env={"GEMINI_API_KEY": "k"}), GeminiProvider)


def test_groq_allowed_in_production():
    env = {"GROQ_API_KEY": "k", "APP_ENV": "production"}
    assert isinstance(get_provider(env=env), GroqProvider)


# ---- Parsing the classifier's JSON reply -----------------------------------

TEXT = "I've been on sertraline for two months and I'm struggling to focus"


def test_parses_flags_with_positions():
    raw = json.dumps({"flags": [{"category": "medical", "span": "sertraline", "confidence": 0.9}]})
    result = parse_classification(raw, TEXT, "groq", "m")
    assert not result.parse_failed
    [flag] = result.flags
    assert (flag.category, flag.span, flag.confidence) == ("MEDICAL", "sertraline", 0.9)
    assert TEXT[flag.start:flag.end] == "sertraline"


def test_empty_flags_is_clean():
    result = parse_classification('{"flags": []}', TEXT, "groq", "m")
    assert result.flags == [] and not result.parse_failed


@pytest.mark.parametrize("raw", ["not json", '{"other": 1}', '{"flags": "x"}', ""])
def test_malformed_reply_marked_as_parse_failure(raw):
    result = parse_classification(raw, TEXT, "groq", "m")
    assert result.parse_failed and result.flags == []


def test_drops_unknown_categories_and_spans_not_in_text():
    raw = json.dumps({"flags": [
        {"category": "FINANCIAL", "span": "sertraline"},
        {"category": "MEDICAL", "span": "depression"},
    ]})
    assert parse_classification(raw, TEXT, "groq", "m").flags == []


def test_classify_uses_provider_reply(monkeypatch):
    provider = get_provider(env={"GROQ_API_KEY": "k"})
    monkeypatch.setattr(provider, "_complete_json",
                        lambda system, text: '{"flags": [{"category": "MEDICAL", "span": "sertraline"}]}')
    result = provider.classify(TEXT)
    assert [f.span for f in result.flags] == ["sertraline"]
    assert (result.provider, result.prompt_version) == ("groq", "context_detector_v1")


# ---- Redaction ---------------------------------------------------------------

def test_redacts_spans():
    text = "My ID is 9203105800089, email t.m@gmail.com"
    spans = [(9, 22, "sa_id"), (30, 43, "email")]
    assert redact(text, spans) == "My ID is [REDACTED_SA_ID], email [REDACTED_EMAIL]"


def test_redact_merges_overlaps_and_keeps_clean_text():
    assert redact("abc 123456 xyz", [(4, 8, "a"), (6, 10, "b")]) == "abc [REDACTED_A] xyz"
    assert redact("nothing here", []) == "nothing here"


def test_redact_rejects_bad_span():
    with pytest.raises(ValueError):
        redact("short", [(2, 99, "x")])
