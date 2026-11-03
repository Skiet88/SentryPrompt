from __future__ import annotations

from collections.abc import Sequence
from typing import Self

import httpx

from app.domain import ChatMessage
from app.exception import ProviderError

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

    def _post(self, payload: dict) -> str:
        try:
            response = httpx.post(self._url, json={"model": self.model, "stream": False, **payload}, timeout=60)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise ProviderError(f"Ollama request failed: {exc}") from exc

    def complete_json(self, system_prompt: str, user_text: str) -> str:
        return self._post({
            "format": "json",
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        })

    def chat(self, messages: Sequence[ChatMessage]) -> str:
        return self._post({"messages": [{"role": m.role.value, "content": m.content} for m in messages]})
