from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain import SourceChannel

from .screening_outcome import ScreeningOutcome


class IScreeningService(ABC):
    @abstractmethod
    async def screen(self, raw_text: str, channel: SourceChannel | str) -> ScreeningOutcome:
        """Screen one prompt with both detectors and explain every flag."""
