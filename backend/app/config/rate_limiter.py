"""Sliding-window rate limiting (SECURITY_RULES.md §4).

In memory, so limits apply per server process. A deployment running several
processes would need a shared store (e.g. Redis); that is a deployment-time
change behind the same RateLimiter interface.
"""

from __future__ import annotations

import math
import time
from abc import ABC, abstractmethod
from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass

DEFAULT_MAX_TRACKED_KEYS = 10_000


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int = 0


class RateLimiter(ABC):
    @abstractmethod
    def hit(self, key: str) -> RateLimitDecision:
        """Record one request for key, or refuse it if the limit is reached."""


class SlidingWindowRateLimiter(RateLimiter):
    def __init__(
        self,
        limit: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
        max_tracked_keys: int = DEFAULT_MAX_TRACKED_KEYS,
    ):
        if limit <= 0 or window_seconds <= 0 or max_tracked_keys <= 0:
            raise ValueError("limit, window_seconds and max_tracked_keys must be positive")
        self._limit = limit
        self._window = window_seconds
        self._clock = clock
        self._max_keys = max_tracked_keys
        self._hits: OrderedDict[str, deque[float]] = OrderedDict()

    def hit(self, key: str) -> RateLimitDecision:
        now = self._clock()
        hits = self._hits.pop(key, None) or deque()
        while hits and hits[0] <= now - self._window:
            hits.popleft()

        if len(hits) >= self._limit:
            self._remember(key, hits)
            retry_after = max(1, math.ceil(hits[0] + self._window - now))
            return RateLimitDecision(allowed=False, retry_after_seconds=retry_after)

        hits.append(now)
        self._remember(key, hits)
        return RateLimitDecision(allowed=True)

    def _remember(self, key: str, hits: deque[float]) -> None:
        # Most recently used last; evict the least recently seen keys so a
        # flood of distinct clients cannot exhaust memory.
        self._hits[key] = hits
        while len(self._hits) > self._max_keys:
            self._hits.popitem(last=False)


@dataclass(frozen=True, slots=True)
class RateLimitPolicy:
    """A per-client limit plus one shared limit across all clients."""

    per_client: RateLimiter
    global_limit: RateLimiter

    def check(self, client_key: str) -> RateLimitDecision:
        decision = self.per_client.hit(client_key)
        if not decision.allowed:
            return decision
        return self.global_limit.hit("global")
