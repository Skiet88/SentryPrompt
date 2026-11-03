"""
Runs the context-aware detector (and the aggregated rule + context verdict)
against docs/evaluation/TEST_SET.csv, using whichever LLM provider is
selected by LLM_PROVIDER (groq by default; see backend/.env.example).

Mirrors the live pipeline: rule-based flags are redacted locally first, then
only the redacted text is sent to the provider.

Usage (from the repo root):
    pip install -r backend/requirements.txt
    export GROQ_API_KEY=...            # free key from console.groq.com
    python run_context_eval.py         # or: LLM_PROVIDER=gemini python run_context_eval.py
"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

from app.llm import ProviderError, get_provider  # noqa: E402
from app.screening.redaction import redact  # noqa: E402
from run_rule_eval import TEST_SET_PATH, find_rule_flags, load_rows  # noqa: E402

DELAY_SECONDS = 2.5  # stays under free-tier per-minute request limits


def metrics(outcomes):
    tp, fp, fn, tn = (outcomes.count(k) for k in ("TP", "FP", "FN", "TN"))
    div = lambda a, b: round(a / b, 4) if b else None
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "precision": div(tp, tp + fp), "recall": div(tp, tp + fn),
            "false_positive_rate": div(fp, fp + tn), "accuracy": div(tp + tn, len(outcomes))}


def outcome(predicted, actual):
    return {(True, True): "TP", (True, False): "FP", (False, True): "FN", (False, False): "TN"}[(predicted, actual)]


def main():
    try:
        provider = get_provider()
    except ProviderError as exc:
        sys.exit(f"Cannot start: {exc}")

    rows = load_rows()
    details, latencies, parse_failures = [], [], 0
    for i, row in enumerate(rows):
        text = row["sampleText"]
        actual = row["groundTruthLabel"].strip().upper() == "FLAG"
        rule_flags = find_rule_flags(text)
        safe_text = redact(text, [(f["start"], f["end"], f["category"]) for f in rule_flags])

        started = time.perf_counter()
        try:
            result = provider.classify(safe_text)
        except ProviderError as exc:
            sys.exit(f"{row['entryId']}: {exc}")
        latencies.append(time.perf_counter() - started)
        parse_failures += result.parse_failed

        context_flag = bool(result.flags)
        aggregated_flag = context_flag or bool(rule_flags)
        details.append({
            "entryId": row["entryId"], "category": row["groundTruthCategory"],
            "groundTruth": "FLAG" if actual else "NO_FLAG",
            "contextOutcome": outcome(context_flag, actual),
            "aggregatedOutcome": outcome(aggregated_flag, actual),
            "contextCategories": sorted({f.category for f in result.flags}),
            "parseFailed": result.parse_failed,
        })
        print(f"{row['entryId']}  context={details[-1]['contextOutcome']}  "
              f"aggregated={details[-1]['aggregatedOutcome']}  {details[-1]['contextCategories']}")
        if i < len(rows) - 1:
            time.sleep(DELAY_SECONDS)

    latencies.sort()
    summary = {
        "provider": provider.name, "model": provider.model, "prompt_version": result.prompt_version,
        "n_entries": len(rows), "parse_failures": parse_failures,
        "median_latency_s": round(latencies[len(latencies) // 2], 3),
        "max_latency_s": round(latencies[-1], 3),
        "context_aware": metrics([d["contextOutcome"] for d in details]),
        "aggregated": metrics([d["aggregatedOutcome"] for d in details]),
    }
    print(json.dumps(summary, indent=2))
    out = TEST_SET_PATH.parent / f"context_eval_results_{provider.name}.json"
    out.write_text(json.dumps({"summary": summary, "details": details}, indent=2), encoding="utf-8")
    print(f"Saved {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
