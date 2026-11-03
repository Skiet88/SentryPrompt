from app.config.lazy import Lazy


def test_builds_once_on_first_use():
    calls = []
    lazy = Lazy(lambda: calls.append(1) or "value")
    assert calls == []
    assert lazy.get() == "value" and lazy.get() == "value"
    assert calls == [1]
