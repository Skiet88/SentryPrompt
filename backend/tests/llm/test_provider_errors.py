import pytest

from app.exception import ProviderError
from app.llm.provider_errors import http_error, network_error, safe_error_code, unexpected_error


@pytest.mark.parametrize(
    "value, expected",
    [
        ("model_not_found", "model_not_found"),
        ("Invalid_Request_Error", "invalid_request_error"),
        ("NOT_FOUND", "not_found"),
        ("The model `x` does not exist", None),
        ("a" * 65, None),
        (None, None),
        (404, None),
    ],
)
def test_safe_error_code_accepts_only_code_like_values(value, expected):
    assert safe_error_code(value) == expected


def test_http_error_summary():
    error = http_error("groq", 404, "model_not_found")
    assert isinstance(error, ProviderError)
    assert str(error) == "groq request failed: HTTP 404 model_not_found"
    assert (error.provider, error.provider_status, error.provider_error_code) == (
        "groq",
        404,
        "model_not_found",
    )


def test_free_text_codes_are_dropped():
    error = http_error("groq", 400, "failed_generation: My ID is 9203105800089")
    assert str(error) == "groq request failed: HTTP 400"
    assert "9203105800089" not in str(error)


def test_network_and_unexpected_errors():
    assert str(network_error("ollama", "timeout")) == "ollama request failed: timeout"
    error = unexpected_error("gemini", RuntimeError("secret detail"))
    assert str(error) == "gemini request failed: RuntimeError"
    assert "secret" not in str(error)
