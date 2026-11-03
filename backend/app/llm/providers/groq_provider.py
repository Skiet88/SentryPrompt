from __future__ import annotations

from collections.abc import Sequence
from typing import Self

from app.domain import ChatMessage
from app.exception import ConfigurationError, ProviderError

from ..config import LLMConfig
from ..provider import LLMProvider
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
        from groq import Groq

        self._client = Groq(api_key=api_key)

    @classmethod
    def from_config(cls, config: LLMConfig) -> Self:
        return cls(model=config.groq_model, api_key=config.groq_api_key)

    def _create(self, **kwargs) -> str:
        try:
            response = self._client.chat.completions.create(model=self.model, **kwargs)
        except Exception as exc:
            raise ProviderError(f"Groq request failed: {exc}") from exc
        return response.choices[0].message.content or ""

    def complete_json(self, system_prompt: str, user_text: str) -> str:
        return self._create(
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        )

    def chat(self, messages: Sequence[ChatMessage]) -> str:
        return self._create(messages=[{"role": m.role.value, "content": m.content} for m in messages])
