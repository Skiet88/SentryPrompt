from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Self

from app.exception import ConfigurationError

from ..chat_message import ChatMessage
from ..config import LLMConfig
from ..provider import LLMProvider
from ..provider_errors import http_error, network_error, unexpected_error
from ..registry import provider_registry


@provider_registry.register
class GroqProvider(LLMProvider):
    """Default provider. Groq's API terms prohibit training on customer data."""

    name = "groq"
    may_train_on_free_tier = False

    def __init__(self, model: str, api_key: str):
        super().__init__(model)
        if not api_key:
            raise ConfigurationError("GROQ_API_KEY is not set")
        from groq import AsyncGroq

        self._client = AsyncGroq(api_key=api_key)

    @classmethod
    def from_config(cls, config: LLMConfig) -> Self:
        return cls(model=config.groq_model, api_key=config.groq_api_key)

    async def _create(self, **kwargs: Any) -> str:
        import groq

        try:
            response = await self._client.chat.completions.create(model=self.model, **kwargs)
        except groq.APIStatusError as exc:
            raise http_error(self.name, exc.status_code, _groq_error_code(exc.body)) from None
        except groq.APITimeoutError:
            raise network_error(self.name, "timeout") from None
        except groq.APIConnectionError:
            raise network_error(self.name, "connection_error") from None
        except Exception as exc:
            raise unexpected_error(self.name, exc) from None
        return response.choices[0].message.content or ""

    async def model_is_available(self) -> bool | None:
        import groq

        try:
            models = await self._client.models.list()
        except groq.APIStatusError as exc:
            raise http_error(self.name, exc.status_code, _groq_error_code(exc.body)) from None
        except groq.APIError:
            raise network_error(self.name, "connection_error") from None
        return self.model in {m.id for m in models.data}

    async def complete_json(self, system_prompt: str, user_text: str) -> str:
        return await self._create(
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        )

    async def chat(self, messages: Sequence[ChatMessage]) -> str:
        return await self._create(messages=[{"role": m.role.value, "content": m.content} for m in messages])


def _groq_error_code(body: object) -> object:
    """Groq error bodies look like {"error": {"code": ..., "type": ...}}."""
    if isinstance(body, dict):
        error = body.get("error", body)
        if isinstance(error, dict):
            return error.get("code") or error.get("type")
    return None
