from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Self

from app.domain import MessageRole
from app.exception import ConfigurationError

from ..chat_message import ChatMessage
from ..config import LLMConfig
from ..provider import LLMProvider
from ..provider_errors import http_error, unexpected_error
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

    async def _generate(self, contents: Any, config: Any = None) -> str:
        from google.genai import errors

        try:
            response = await self._client.aio.models.generate_content(
                model=self.model, contents=contents, config=config
            )
        except errors.APIError as exc:
            raise http_error(self.name, exc.code, exc.status) from None
        except Exception as exc:
            raise unexpected_error(self.name, exc) from None
        return response.text or ""

    async def complete_json(self, system_prompt: str, user_text: str) -> str:
        from google.genai import types

        return await self._generate(
            user_text,
            types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0,
                response_mime_type="application/json",
            ),
        )

    async def chat(self, messages: Sequence[ChatMessage]) -> str:
        from google.genai import types

        contents = [
            types.Content(
                role="model" if m.role is MessageRole.ASSISTANT else "user",
                parts=[types.Part(text=m.content)],
            )
            for m in messages
        ]
        return await self._generate(contents)
