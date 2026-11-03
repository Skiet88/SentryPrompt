import asyncio

import pytest

from app.factory.evaluation_log_entry_factory import build_evaluation_log_entry
from app.repository.evaluation_log_entry_repository import EvaluationLogEntryRepository
from app.repository.memory.evaluation_log_entry_repository import InMemoryEvaluationLogEntryRepository


def run(coroutine):
    return asyncio.run(coroutine)


def test_saves_and_finds():
    repo = InMemoryEvaluationLogEntryRepository()
    entry = build_evaluation_log_entry("result-1", "unflagged")
    run(repo.save(entry))
    assert run(repo.find_by_id(entry.log_id)) == entry
    assert run(repo.find_by_result_id("result-1")) == [entry]
    assert run(repo.find_all()) == [entry]


def test_is_append_only():
    repo = InMemoryEvaluationLogEntryRepository()
    entry = build_evaluation_log_entry("result-1", "unflagged")
    run(repo.save(entry))
    with pytest.raises(ValueError, match="append-only"):
        run(repo.save(entry))
    assert not hasattr(EvaluationLogEntryRepository, "delete")


def test_capacity_drops_oldest():
    repo = InMemoryEvaluationLogEntryRepository(capacity=2)
    entries = [build_evaluation_log_entry(f"r{i}", "unflagged") for i in range(3)]
    for entry in entries:
        run(repo.save(entry))
    assert run(repo.find_all()) == entries[1:]
