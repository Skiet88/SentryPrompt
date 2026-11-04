import asyncio

from app.factory.evaluation_log_entry_factory import build_evaluation_log_entry
from app.factory.flagged_span_factory import build_flagged_span
from app.factory.screening_result_factory import build_screening_result
from app.repository.memory.screening_records import (
    InMemoryFlaggedSpanRepository,
    InMemoryScreeningRecordWriter,
    InMemoryScreeningResultRepository,
)


def run(coroutine):
    return asyncio.run(coroutine)


def test_writer_saves_result_spans_and_entry():
    writer = InMemoryScreeningRecordWriter()
    result = build_screening_result("prompt-1", "FLAG", "NO_FLAG")
    span = build_flagged_span(result.result_id, 0, 5, "rule", "cat-1")
    entry = build_evaluation_log_entry(result.result_id, "flagged", "cat-1")
    run(writer.record(result, [span], entry))
    assert run(writer.results.find_by_prompt_id("prompt-1")) == [result]
    assert run(writer.spans.find_by_result_id(result.result_id)) == [span]
    assert run(writer.spans.find_by_id(span.span_id)) == span
    assert run(writer.log.find_by_result_id(result.result_id)) == [entry]


def test_repositories_are_bounded():
    results = InMemoryScreeningResultRepository(capacity=2)
    spans = InMemoryFlaggedSpanRepository(capacity=2)
    for i in range(3):
        result = build_screening_result(f"p{i}", "NO_FLAG", "NO_FLAG")
        run(results.save(result))
        run(spans.save(build_flagged_span(result.result_id, 0, 1, "rule", "c")))
    assert len(run(results.find_all())) == 2 and len(run(spans.find_all())) == 2
    assert run(results.find_by_id("missing")) is None
