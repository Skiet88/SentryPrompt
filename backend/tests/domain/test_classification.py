from app.domain import ClassificationResult
from app.factory.context_flag_factory import build_context_flag


def test_is_flagged_reflects_flags():
    clean = ClassificationResult("groq", "m", "v1")
    flagged = ClassificationResult("groq", "m", "v1", flags=(build_context_flag("MEDICAL", "x", "x"),))
    assert not clean.is_flagged
    assert flagged.is_flagged
