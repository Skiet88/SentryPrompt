"""
Runs the REAL rule-based detector (ported verbatim from the frontend's
src/lib/screening.ts RULE_PATTERNS) against docs/evaluation/TEST_SET.csv.

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

# ---- Ported verbatim from src/lib/screening.ts RULE_PATTERNS ----
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
     "This looks like a bank account or card number..."),
    ("address", re.compile(
        r"\b\d{1,4}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Close|Cl)\b"),
     "A physical address is location data..."),
]


def find_rule_flags(text: str):
    flags = []
    for category, regex, explain in RULE_PATTERNS:
        for m in regex.finditer(text):
            match_text = m.group(0)
            # Same false-positive guard as the TS original:
            # skip absurdly short student-number matches
            if category == "student_number" and len(match_text) < 7:
                continue
            flags.append({
                "category": category,
                "start": m.start(),
                "end": m.end(),
                "match": match_text,
            })
    return flags


def main():
    rows = []
    with open("docs/evaluation/TEST_SET.csv", newline="", encoding="utf-8") as f:
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
        "detector": "rule-based (verbatim port of screening.ts RULE_PATTERNS)",
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
    with open("/home/claude/rule_based_eval_results.json", "w") as f:
        json.dump({"summary": summary, "details": detail_rows}, f, indent=2)


if __name__ == "__main__":
    main()
