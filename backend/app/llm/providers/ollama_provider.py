from __future__ import annotations

from collections.abc import Sequence
from typing import Self

import httpx

from app.exception import ProviderError

from ..chat_message import ChatMessage
from ..config import LLMConfig
from ..provider import LLMProvider
from ..registry import provider_registry


@provider_registry.register
class OllamaProvider(LLMProvider):
    """Free, fully local provider for offline evaluation runs."""

    name = "ollama"
    may_train_on_free_tier = False

    def __init__(self, model: str, base_url: str):
        super().__init__(model)
        self._url = base_url.rstrip("/") + "/api/chat"

    @classmethod
    def from_config(cls, config: LLMConfig) -> Self:
        return cls(model=config.ollama_model, base_url=config.ollama_url)

    async def _post(self, payload: dict[str, object]) -> str:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    self._url, json={"model": self.model, "stream": False, **payload}
                )
            response.raise_for_status()
            content = response.json()["message"]["content"]
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise ProviderError(f"Ollama request failed: {exc}") from exc
        if not isinstance(content, str):
            raise ProviderError("Ollama returned a non-text reply")
        return content

    async def complete_json(self, system_prompt: str, user_text: str) -> str:
        return await self._post(
            {
                "format": "json",
                "options": {"temperature": 0},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
            }
        )

    async def chat(self, messages: Sequence[ChatMessage]) -> str:
        return await self._post(
            {"messages": [{"role": m.role.value, "content": m.content} for m in messages]}
        )
