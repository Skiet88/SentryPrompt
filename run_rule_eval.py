"""
Runs the backend's rule-based detector against docs/evaluation/TEST_SET.csv.

The detector and its patterns live in the backend
(backend/app/screening/rules/, patterns in detection_categories.json, NFR-005),
so this evaluation always measures the code that actually runs in the app.

History: the patterns were first a verbatim port of the UI prototype's
src/lib/screening.ts RULE_PATTERNS. Revision 2 fixed overlapping matches
(resolved by category priority), added a keyword-anchored bank_account rule
(TS-005) and a Luhn check for card numbers. Revision 3 moved the rules into
the backend, bounded every repetition to remove a ReDoS weakness in the email
pattern, and fixed the phone pattern so a leading '+' is part of the match.
Results are unchanged from Revision 2 (see backend tests,
test_evaluation_parity.py).

This mirrors EVALUATION_HARNESS_DESIGN.md's design: call the detector
directly, bypass any API/UI layer, compare to ground truth, compute
precision/recall/false-positive rate for the RULE-BASED detector only.
The context-aware detector is evaluated separately by run_context_eval.py.
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

from app.screening.rules.rule_based_detector import RuleBasedDetector  # noqa: E402
from app.screening.rules.rule_source import JsonRuleSource  # noqa: E402

# Paths are relative to this script, so it runs from any directory or OS.
EVAL_DIR = ROOT / "docs" / "evaluation"
TEST_SET_PATH = EVAL_DIR / "TEST_SET.csv"
RESULTS_PATH = EVAL_DIR / "rule_based_eval_results.json"

DETECTOR = RuleBasedDetector(JsonRuleSource().load())


def find_rule_flags(text: str):
    """Rule-based flags for text, as dicts (also used by run_context_eval.py)."""
    return [
        {"category": span.category, "start": span.start, "end": span.end, "match": text[span.start:span.end]}
        for span in DETECTOR.detect_now(text).spans
    ]


def load_rows():
    with open(TEST_SET_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 40, f"expected 40 entries, got {len(rows)}"
    return rows


def main():
    rows = load_rows()

    tp = fp = fn = tn = 0
    detail_rows = []

    for row in rows:
        entry_id = row["entryId"]
        text = row["sampleText"]
        ground_truth = row["groundTruthLabel"].strip().upper()  # FLAG / NO_FLAG
        category = row["groundTruthCategory"]

        flags = find_rule_flags(text)
        predicted_flag = len(flags) > 0

        actual_flag = ground_truth == "FLAG"

        if predicted_flag and actual_flag:
            outcome = "TP"; tp += 1
        elif predicted_flag and not actual_flag:
            outcome = "FP"; fp += 1
        elif not predicted_flag and actual_flag:
            outcome = "FN"; fn += 1
        else:
            outcome = "TN"; tn += 1

        detail_rows.append({
            "entryId": entry_id,
            "category": category,
            "groundTruth": ground_truth,
            "predicted": "FLAG" if predicted_flag else "NO_FLAG",
            "outcome": outcome,
            "matchedCategories": sorted(set(fl["category"] for fl in flags)),
        })

    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    fpr = fp / (fp + tn) if (fp + tn) else float("nan")
    accuracy = (tp + tn) / len(rows)

    # Taxonomy-scoped recall: SPECIFICATION.md §3 assigns MEDICAL and
    # INSTITUTIONAL to the context-aware tier only. Counting rule-based
    # misses on those as "failures" would misrepresent what this detector
    # was ever designed to catch. This second recall figure restricts to
    # the categories the taxonomy actually assigns to rule-based detection
    # (ID_NUMBER, FINANCIAL, CONTACT_LOCATION).
    RULE_TIER_CATEGORIES = {"ID_NUMBER", "FINANCIAL", "CONTACT_LOCATION"}
    scoped_tp = scoped_fn = 0
    for d in detail_rows:
        if d["groundTruth"] == "FLAG" and d["category"] in RULE_TIER_CATEGORIES:
            if d["outcome"] == "TP":
                scoped_tp += 1
            elif d["outcome"] == "FN":
                scoped_fn += 1
    scoped_recall = scoped_tp / (scoped_tp + scoped_fn) if (scoped_tp + scoped_fn) else float("nan")

    summary = {
        "detector": "rule-based (backend RuleBasedDetector, detection_categories.json)",
        "n_entries": len(rows),
        "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        "precision": round(precision, 4),
        "recall_all_categories": round(recall, 4),
        "recall_rule_tier_categories_only": round(scoped_recall, 4),
        "false_positive_rate": round(fpr, 4),
        "accuracy": round(accuracy, 4),
        "note": "MEDICAL/INSTITUTIONAL FLAG entries are structural misses by design "
                "(SPECIFICATION.md §3 assigns them to the context-aware tier only, "
                "not a rule-based detector defect). recall_rule_tier_categories_only "
                "excludes them for a fairer per-tier figure.",
    }

    print(json.dumps(summary, indent=2))
    print()
    print("Per-entry detail:")
    print(f"{'ID':6} {'Category':16} {'GroundTruth':10} {'Predicted':10} {'Outcome':6} Matched")
    for d in detail_rows:
        print(f"{d['entryId']:6} {d['category']:16} {d['groundTruth']:10} "
              f"{d['predicted']:10} {d['outcome']:6} {','.join(d['matchedCategories'])}")

    # Save machine-readable results for the report
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "details": detail_rows}, f, indent=2)


if __name__ == "__main__":
    main()
