import pytest

from app.config.rate_limiter import RateLimitPolicy, SlidingWindowRateLimiter


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_allows_up_to_limit_then_refuses_with_retry_after():
    clock = Clock()
    limiter = SlidingWindowRateLimiter(limit=3, window_seconds=60, clock=clock)
    assert all(limiter.hit("a").allowed for _ in range(3))
    clock.now += 10
    refused = limiter.hit("a")
    assert not refused.allowed and refused.retry_after_seconds == 50


def test_window_slides():
    clock = Clock()
    limiter = SlidingWindowRateLimiter(limit=2, window_seconds=60, clock=clock)
    limiter.hit("a")
    clock.now += 30
    limiter.hit("a")
    assert not limiter.hit("a").allowed
    clock.now += 31  # first hit is now outside the window
    assert limiter.hit("a").allowed


def test_refused_requests_do_not_count():
    clock = Clock()
    limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60, clock=clock)
    limiter.hit("a")
    for _ in range(5):
        limiter.hit("a")
    clock.now += 61
    assert limiter.hit("a").allowed


def test_keys_are_independent():
    limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60, clock=Clock())
    assert limiter.hit("a").allowed and limiter.hit("b").allowed
    assert not limiter.hit("a").allowed


def test_tracked_keys_are_bounded():
    limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60, clock=Clock(), max_tracked_keys=100)
    for i in range(1000):
        limiter.hit(f"client-{i}")
    assert len(limiter._hits) == 100


@pytest.mark.parametrize("kwargs", [{"limit": 0}, {"window_seconds": 0}, {"max_tracked_keys": 0}])
def test_rejects_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        SlidingWindowRateLimiter(**{"limit": 1, "window_seconds": 1, **kwargs})


def test_policy_checks_client_then_global():
    clock = Clock()
    policy = RateLimitPolicy(
        per_client=SlidingWindowRateLimiter(2, 60, clock=clock),
        global_limit=SlidingWindowRateLimiter(3, 60, clock=clock),
    )
    assert policy.check("a").allowed and policy.check("a").allowed
    assert not policy.check("a").allowed  # client limit
    assert policy.check("b").allowed
    assert not policy.check("c").allowed  # global limit
