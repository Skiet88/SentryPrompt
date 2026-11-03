"""
Runs the rule-based detector against docs/evaluation/TEST_SET.csv.

Originally a verbatim port of the UI prototype's src/lib/screening.ts
RULE_PATTERNS (prototype code lives outside this repo). Revised to fix two
defects found in the first evaluation run:
  1. Overlapping matches: a 13-digit SA ID also matched bank_card (and a
     card number could also match student_number). Overlapping spans are now
     resolved by category priority, so each span gets exactly one label.
  2. Missed bank account numbers (TS-005): bank_card only covered 13-19
     digits. A keyword-anchored bank_account rule now catches 8-12 digit
     account numbers ("account number is ...").
bank_card matches must also pass the Luhn checksum, which every real card
number satisfies, so random long digit runs are not reported as cards.

This mirrors EVALUATION_HARNESS_DESIGN.md's design: call the detector
directly, bypass any API/UI layer, compare to ground truth, compute
precision/recall/false-positive rate for the RULE-BASED detector only.

The context-aware (Ollama/llama3.2) detector is NOT run here — that
requires the local LLM backend, which is a Testing Phase / build-phase
dependency not present at Design Phase. Those rows are left pending,
consistent with EVALUATION_HARNESS_DESIGN.md's explicit anti-fabrication
stance.
"""

import csv
import re
import json
from pathlib import Path

# Paths are relative to this script, so it runs from any directory or OS.
EVAL_DIR = Path(__file__).resolve().parent / "docs" / "evaluation"
TEST_SET_PATH = EVAL_DIR / "TEST_SET.csv"
RESULTS_PATH = EVAL_DIR / "rule_based_eval_results.json"

# ---- Rule patterns (keep src/lib/screening.ts in sync with these) ----
# (category, python-translated regex, explanation)
RULE_PATTERNS = [
    ("sa_id", re.compile(r"\b\d{13}\b"),
     "This looks like a South African ID number..."),
    ("student_number", re.compile(r"\b(?:stu(?:dent)?[\s#-]*)?[0-9]{7,9}\b", re.IGNORECASE),
     "This resembles a student number..."),
    ("phone", re.compile(r"\b(?:\+?27|0)\s?[6-8]\d(?:[\s-]?\d){7}\b"),
     "A phone number is direct contact information..."),
    ("email", re.compile(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", re.IGNORECASE),
     "Email addresses are personal contact information..."),
    ("bank_card", re.compile(r"\b(?:\d[ -]?){13,19}\b"),
     "This looks like a bank card number..."),
    ("bank_account", re.compile(
        r"\b(?:account|acc|acct)\.?(?:\s*(?:number|no\.?|num|#))?(?:\s*(?:is|:|=))?\s*\d{8,12}\b",
        re.IGNORECASE),
     "This looks like a bank or loan account number..."),
    ("address", re.compile(
        r"\b\d{1,4}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Close|Cl)\b"),
     "A physical address is location data..."),
]


# When two matches overlap, the earlier category in this list wins.
# Most specific first: a 13-digit number is an SA ID before it is a card.
CATEGORY_PRIORITY = ["sa_id", "bank_card", "bank_account", "phone",
                     "email", "address", "student_number"]


def luhn_valid(text: str) -> bool:
    digits = [int(c) for c in text if c.isdigit()][::-1]
    total = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def find_rule_flags(text: str):
    candidates = []
    for category, regex, explain in RULE_PATTERNS:
        for m in regex.finditer(text):
            match_text = m.group(0)
            # Same false-positive guard as the TS original:
            # skip absurdly short student-number matches
            if category == "student_number" and len(match_text) < 7:
                continue
            if category == "bank_card" and not luhn_valid(match_text):
                continue
            candidates.append({
                "category": category,
                "start": m.start(),
                "end": m.end(),
                "match": match_text,
            })

    # Resolve overlaps: keep the highest-priority match for any span.
    candidates.sort(key=lambda f: (CATEGORY_PRIORITY.index(f["category"]), f["start"]))
    flags = []
    for c in candidates:
        if all(c["end"] <= f["start"] or c["start"] >= f["end"] for f in flags):
            flags.append(c)
    flags.sort(key=lambda f: f["start"])
    return flags


def main():
    rows = []
    with open(TEST_SET_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    assert len(rows) == 40, f"expected 40 entries, got {len(rows)}"

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
        "detector": "rule-based (screening.ts RULE_PATTERNS + overlap resolution, Luhn check, bank_account rule)",
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
