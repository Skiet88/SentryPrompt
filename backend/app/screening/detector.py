"""Detector interface (Strategy). The screening service runs every detector
on each prompt in parallel (FR-004) without knowing which kind it is."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from app.domain import DetectorSource

from .detection import DetectionResult


class Detector(ABC):
    source: ClassVar[DetectorSource]

    @abstractmethod
    async def detect(self, text: str) -> DetectionResult:
        """Return the spans this detector flags in text, and its verdict."""
