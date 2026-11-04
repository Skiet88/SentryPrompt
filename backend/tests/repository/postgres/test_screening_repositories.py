import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.domain import Verdict
from app.factory.evaluation_log_entry_factory import build_evaluation_log_entry
from app.factory.flagged_span_factory import build_flagged_span
from app.factory.screening_result_factory import build_screening_result
from app.repository.postgres.screening_records import (
    PostgresEvaluationLogEntryRepository,
    PostgresFlaggedSpanRepository,
    PostgresScreeningRecordWriter,
    PostgresScreeningResultRepository,
)
from tests.repository.postgres.conftest import run

CATEGORY = str(uuid.uuid4())


def records(prompt_id: str | None = None):
    result = build_screening_result(prompt_id or str(uuid.uuid4()), "FLAG", "UNAVAILABLE")
    spans = [
        build_flagged_span(result.result_id, 9, 22, "rule", CATEGORY),
        build_flagged_span(result.result_id, 27, 44, "context", CATEGORY),
    ]
    entry = build_evaluation_log_entry(result.result_id, "flagged", CATEGORY)
    return result, spans, entry


def test_writer_saves_everything_and_repositories_read_it_back(engine):
    result, spans, entry = records()
    run(PostgresScreeningRecordWriter(engine).record(result, spans, entry))

    stored = run(PostgresScreeningResultRepository(engine).find_by_id(result.result_id))
    assert stored == result
    assert stored.aggregated_verdict is Verdict.FLAG
    assert run(PostgresScreeningResultRepository(engine).find_by_prompt_id(result.prompt_id)) == [result]
    assert run(PostgresFlaggedSpanRepository(engine).find_by_result_id(result.result_id)) == spans
    assert run(PostgresEvaluationLogEntryRepository(engine).find_by_result_id(result.result_id)) == [entry]


def test_writer_is_all_or_nothing(engine):
    result, spans, _ = records()
    broken_entry = build_evaluation_log_entry(str(uuid.uuid4()), "unflagged")  # unknown result: FK fails
    with pytest.raises(IntegrityError):
        run(PostgresScreeningRecordWriter(engine).record(result, spans, broken_entry))
    assert run(PostgresScreeningResultRepository(engine).find_by_id(result.result_id)) is None
    assert run(PostgresFlaggedSpanRepository(engine).find_all()) == []


def test_individual_repositories_save_and_find(engine):
    result, spans, entry = records()
    run(PostgresScreeningResultRepository(engine).save(result))
    run(PostgresFlaggedSpanRepository(engine).save(spans[0]))
    run(PostgresEvaluationLogEntryRepository(engine).save(entry))
    assert run(PostgresFlaggedSpanRepository(engine).find_by_id(spans[0].span_id)) == spans[0]
    assert run(PostgresEvaluationLogEntryRepository(engine).find_by_id(entry.log_id)) == entry
    assert len(run(PostgresScreeningResultRepository(engine).find_all())) == 1
    assert run(PostgresScreeningResultRepository(engine).find_by_id(str(uuid.uuid4()))) is None


def test_clean_result_without_spans(engine):
    result = build_screening_result(str(uuid.uuid4()), "NO_FLAG", "NO_FLAG")
    entry = build_evaluation_log_entry(result.result_id, "unflagged")
    run(PostgresScreeningRecordWriter(engine).record(result, [], entry))
    assert run(PostgresEvaluationLogEntryRepository(engine).find_all()) == [entry]
