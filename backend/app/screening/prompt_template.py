"""Loads versioned system prompts, so a wording change is a visible new file
and evaluation results always record which version produced them."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.exception import ConfigurationError

PROMPTS_DIR = Path(__file__).parent / "prompts"


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    version: str
    text: str

    @classmethod
    def load(cls, version: str, directory: Path = PROMPTS_DIR) -> PromptTemplate:
        path = directory / f"{version}.txt"
        if not path.is_file():
            raise ConfigurationError(f"Prompt template '{version}' not found in {directory}")
        return cls(version=version, text=path.read_text(encoding="utf-8"))


CONTEXT_DETECTOR_PROMPT_VERSION = "context_detector_v1"
