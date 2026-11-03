from __future__ import annotations

from .base import ChatMessage, LLMProvider, ProviderError


class GeminiProvider(LLMProvider):
    """Alternative provider. The free tier may use prompts to improve Google's
    models, so it is only for made-up/demo data unless billing is enabled."""

    name = "gemini"
    may_train_on_free_tier = True

    def __init__(self, model: str, api_key: str):
        super().__init__(model)
        if not api_key:
            raise ProviderError("GEMINI_API_KEY is not set")
        from google import genai

        self._client = genai.Client(api_key=api_key)

    def _complete_json(self, system: str, text: str) -> str:
        from google.genai import types

        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=text,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=0,
                    response_mime_type="application/json",
                ),
            )
        except Exception as exc:
            raise ProviderError(f"Gemini request failed: {exc}") from exc
        return response.text or ""

    def chat(self, messages: list[ChatMessage]) -> str:
        from google.genai import types

        contents = [
            types.Content(role="model" if m.role == "assistant" else "user",
                          parts=[types.Part(text=m.content)])
            for m in messages
        ]
        try:
            response = self._client.models.generate_content(model=self.model, contents=contents)
        except Exception as exc:
            raise ProviderError(f"Gemini request failed: {exc}") from exc
        return response.text or ""
