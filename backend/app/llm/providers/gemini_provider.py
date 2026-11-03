from __future__ import annotations

from collections.abc import Sequence
from typing import Self

from app.domain import ChatMessage, ChatRole
from app.exception import ConfigurationError, ProviderError

from ..config import LLMConfig
from ..provider import LLMProvider
from ..registry import provider_registry


@provider_registry.register
class GeminiProvider(LLMProvider):
    """Alternative provider. Its free tier may use prompts to improve Google's
    models, so TrainingDataPolicy keeps it to made-up data unless billing is on."""

    name = "gemini"
    may_train_on_free_tier = True

    def __init__(self, model: str, api_key: str):
        super().__init__(model)
        if not api_key:
            raise ConfigurationError("GEMINI_API_KEY is not set")
        from google import genai

        self._client = genai.Client(api_key=api_key)

    @classmethod
    def from_config(cls, config: LLMConfig) -> Self:
        return cls(model=config.gemini_model, api_key=config.gemini_api_key)

    def _generate(self, contents, config=None) -> str:
        try:
            response = self._client.models.generate_content(
                model=self.model, contents=contents, config=config
            )
        except Exception as exc:
            raise ProviderError(f"Gemini request failed: {exc}") from exc
        return response.text or ""

    def complete_json(self, system_prompt: str, user_text: str) -> str:
        from google.genai import types

        return self._generate(
            user_text,
            types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0,
                response_mime_type="application/json",
            ),
        )

    def chat(self, messages: Sequence[ChatMessage]) -> str:
        from google.genai import types

        contents = [
            types.Content(
                role="model" if m.role is ChatRole.ASSISTANT else "user",
                parts=[types.Part(text=m.content)],
            )
            for m in messages
        ]
        return self._generate(contents)
