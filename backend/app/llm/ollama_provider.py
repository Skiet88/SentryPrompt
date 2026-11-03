from __future__ import annotations

import httpx

from .base import ChatMessage, LLMProvider, ProviderError


class OllamaProvider(LLMProvider):
    """Free, fully local provider. Needs Ollama running on the same machine,
    so it suits offline evaluation runs rather than a deployed app."""

    name = "ollama"
    may_train_on_free_tier = False

    def __init__(self, model: str, base_url: str):
        super().__init__(model)
        self._url = base_url.rstrip("/") + "/api/chat"

    def _post(self, payload: dict) -> str:
        try:
            response = httpx.post(self._url, json=payload, timeout=60)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Ollama request failed: {exc}") from exc
        return response.json()["message"]["content"]

    def _complete_json(self, system: str, text: str) -> str:
        return self._post({
            "model": self.model,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
        })

    def chat(self, messages: list[ChatMessage]) -> str:
        return self._post({
            "model": self.model,
            "stream": False,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        })
