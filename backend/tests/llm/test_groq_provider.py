"""GroqProvider error handling, without network calls."""

import asyncio

import groq
import httpx
import pytest

from app.exception import ProviderError
from app.llm.providers.groq_provider import GroqProvider

PROMPT_WITH_ID = "My ID is 9203105800089"


def status_error(status: int, body: object) -> groq.APIStatusError:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(status, request=request)
    return groq.APIStatusError(f"Error code: {status} - {body}", response=response, body=body)


def provider_raising(exc: Exception) -> GroqProvider:
    provider = GroqProvider(model="retired-model", api_key="test-key")

    async def fail(**kwargs):
        raise exc

    provider._client.chat.completions.create = fail
    return provider


def test_model_not_found_gives_safe_summary():
    body = {"error": {"message": "The model `retired-model` does not exist", "code": "model_not_found"}}
    with pytest.raises(ProviderError) as caught:
        asyncio.run(provider_raising(status_error(404, body)).complete_json("system", "text"))
    assert str(caught.value) == "groq request failed: HTTP 404 model_not_found"
    assert caught.value.__cause__ is None and caught.value.__suppress_context__


def test_error_body_with_prompt_content_never_reaches_the_message():
    body = {
        "error": {
            "message": "Failed to generate JSON",
            "type": "invalid_request_error",
            "code": "json_validate_failed",
            "failed_generation": PROMPT_WITH_ID,
        }
    }
    with pytest.raises(ProviderError) as caught:
        asyncio.run(provider_raising(status_error(400, body)).complete_json("system", PROMPT_WITH_ID))
    assert "9203105800089" not in str(caught.value)
    assert str(caught.value) == "groq request failed: HTTP 400 json_validate_failed"


def test_timeout_and_connection_errors():
    request = httpx.Request("POST", "https://api.groq.com")
    for exc, expected in (
        (groq.APITimeoutError(request=request), "timeout"),
        (groq.APIConnectionError(request=request), "connection_error"),
    ):
        with pytest.raises(ProviderError, match=expected):
            asyncio.run(provider_raising(exc).complete_json("system", "text"))


def test_model_is_available():
    provider = GroqProvider(model="openai/gpt-oss-20b", api_key="test-key")

    class Model:
        def __init__(self, model_id: str) -> None:
            self.id = model_id

    class Listing:
        data = (Model("openai/gpt-oss-20b"), Model("openai/gpt-oss-120b"))

    async def listing():
        return Listing()

    provider._client.models.list = listing
    assert asyncio.run(provider.model_is_available()) is True
    provider.model = "llama-3.1-8b-instant"
    assert asyncio.run(provider.model_is_available()) is False
