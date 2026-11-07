from __future__ import annotations

from collections.abc import Sequence
from typing import Self

import httpx

from ..chat_message import ChatMessage
from ..config import LLMConfig
from ..provider import LLMProvider
from ..provider_errors import http_error, network_error
from ..registry import provider_registry


@provider_registry.register
class OllamaProvider(LLMProvider):
    """Free, fully local provider for offline evaluation runs."""

    name = "ollama"
    may_train_on_free_tier = False

    def __init__(self, model: str, base_url: str):
        super().__init__(model)
        base = base_url.rstrip("/")
        self._url = base + "/api/chat"
        self._tags_url = base + "/api/tags"

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
        except httpx.HTTPStatusError as exc:
            raise http_error(self.name, exc.response.status_code) from None
        except httpx.TimeoutException:
            raise network_error(self.name, "timeout") from None
        except httpx.HTTPError:
            raise network_error(self.name, "connection_error") from None
        except (KeyError, TypeError, ValueError):
            raise network_error(self.name, "unreadable_response") from None
        if not isinstance(content, str):
            raise network_error(self.name, "unreadable_response")
        return content

    async def model_is_available(self) -> bool | None:
        """Ollama lists local models as "name:tag"; "llama3.2" means "llama3.2:latest"."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(self._tags_url)
            response.raise_for_status()
            names = {m["name"] for m in response.json()["models"]}
        except httpx.HTTPError:
            raise network_error(self.name, "connection_error") from None
        except (KeyError, TypeError, ValueError):
            raise network_error(self.name, "unreadable_response") from None
        wanted = self.model if ":" in self.model else f"{self.model}:latest"
        return wanted in names

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
