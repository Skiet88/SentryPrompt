"""SECURITY_RULES.md §1: rule regexes must not backtrack catastrophically.

Every configured pattern is timed against inputs designed to trigger
backtracking, at the maximum prompt length (FR-001, 4,000 characters).
"""

import time

import pytest

from app.factory.prompt_factory import MAX_PROMPT_LENGTH

N = MAX_PROMPT_LENGTH
ATTACKS = {
    "digits": "1" * N,
    "digits_spaces": "1 " * (N // 2),
    "digits_dashes": "1-" * (N // 2),
    "spaces": " " * N,
    "dotted_local": ("a." * (N // 4)) + "@" + ("b." * (N // 4 - 1)),
    "at_without_tld": "a" * (N // 2) + "@" + "b" * (N // 2 - 1),
    "dots_domain": "x@" + "a." * (N // 2 - 1),
    "many_ats": "a@" * (N // 2),
    "capitalised_words": "12 " + "Abc " * ((N - 3) // 4),
    "account_spam": "account " * (N // 8),
    "student_separators": "student" + "#" * (N - 20) + "1234",
    "country_codes": "+27 " * (N // 4),
}
# Generous for slow CI machines; vulnerable patterns took 100-200+ ms here.
BUDGET_SECONDS = 0.05


@pytest.mark.parametrize("attack", ATTACKS)
def test_every_rule_is_linear_on_attack_input(rule_set, attack):
    text = ATTACKS[attack]
    assert len(text) <= MAX_PROMPT_LENGTH
    for rule in rule_set.rules:
        started = time.perf_counter()
        list(rule.pattern.finditer(text))
        elapsed = time.perf_counter() - started
        assert elapsed < BUDGET_SECONDS, f"{rule.category.name} took {elapsed * 1000:.0f} ms on {attack}"
