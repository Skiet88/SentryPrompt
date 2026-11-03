import pytest

from app.util.validation import is_blank, is_probability


@pytest.mark.parametrize("value", [None, "", "   ", "\n"])
def test_blank_values(value):
    assert is_blank(value)


def test_non_blank_value():
    assert not is_blank("text")


@pytest.mark.parametrize("value", [0, 0.5, 1, 1.0])
def test_valid_probabilities(value):
    assert is_probability(value)


@pytest.mark.parametrize("value", [-0.1, 1.01, "0.5", True, None])
def test_invalid_probabilities(value):
    assert not is_probability(value)
