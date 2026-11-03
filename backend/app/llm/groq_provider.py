from __future__ import annotations

from .base import ChatMessage, LLMProvider, ProviderError


class GroqProvider(LLMProvider):
    """Default provider. Groq's API terms prohibit training on customer data."""

    name = "groq"
    may_train_on_free_tier = False

    def __init__(self, model: str, api_key: str):
        super().__init__(model)
        if not api_key:
            raise ProviderError("GROQ_API_KEY is not set")
        from groq import Groq

        self._client = Groq(api_key=api_key)

    def _complete_json(self, system: str, text: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": text},
                ],
            )
        except Exception as exc:
            raise ProviderError(f"Groq request failed: {exc}") from exc
        return response.choices[0].message.content or ""

    def chat(self, messages: list[ChatMessage]) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
            )
        except Exception as exc:
            raise ProviderError(f"Groq request failed: {exc}") from exc
        return response.choices[0].message.content or ""
