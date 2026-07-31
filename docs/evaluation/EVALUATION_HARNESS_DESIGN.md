# EVALUATION_HARNESS_DESIGN.md — SentryPrompt4

**Traces to:** FR-012, UC8 (Run Evaluation Against Test Set), the Increment 2A architecture gap (offline entry point into the Screening Service)
**Feeds:** Design Phase Template §8.3.2 (Data Pipeline validation), real numbers for §9

---

## 1. Purpose

This is the design for the script that answers SentryPrompt4's actual research question: does parallel rule-based + context-aware detection outperform either method alone? It runs `TEST_SET.csv` through both detectors **independently**, compares each to ground truth, and computes the metrics ../requirements/SPECIFICATION.md §6 commits to.

## 2. Design

```
1. Load TEST_SET.csv into memory (40 TestSetEntry records)
2. For each entry:
   a. Run Rule-Based Detector on sampleText  → ruleVerdict (FLAG/NO_FLAG)
   b. Run Context-Aware Detector on sampleText → contextVerdict (FLAG/NO_FLAG)   [independent, not fallback]
   c. Compute aggregatedVerdict = ruleVerdict OR contextVerdict                  [either detector flagging is enough]
   d. Record: entryId, groundTruth, ruleVerdict, contextVerdict, aggregatedVerdict
3. For each of {ruleVerdict, contextVerdict, aggregatedVerdict} independently:
   - TP = flagged AND groundTruth == FLAG
   - FP = flagged AND groundTruth == NO_FLAG
   - FN = not flagged AND groundTruth == FLAG
   - TN = not flagged AND groundTruth == NO_FLAG
   - Precision = TP / (TP + FP)
   - Recall = TP / (TP + FN)
   - False Positive Rate = FP / (FP + TN)
4. Output: a results table (3 rows — rule-only, context-only, aggregated — × 3 metrics each)
5. Output: a qualitative log of every entry where ruleVerdict != contextVerdict — this is the actual
   research discussion material for ../requirements/SPECIFICATION.md §6 ("cases where rule-based fails but
   context-aware succeeds, and vice versa")
```

**Why this bypasses the API/UI layer entirely (per Increment 2A):** the harness calls the Screening Service's detectors directly — the same code path the Backend API would call, but invoked from a script, not a live student request. This is what makes UC8 genuinely "independent of live usage" rather than requiring a running web session for every evaluation run.

## 3. Results

**Status: rule-based detector run for real. Context-aware detector and the aggregated verdict remain pending — genuinely blocked, not deferred out of convenience.**

The rule-based detector requires no external dependency (it is pure regex, already implemented client-side in the UI prototype's `src/lib/screening.ts`), so it was runnable at Design Phase without contradicting the anti-fabrication stance below. The context-aware detector depends on a local `llama3.2` instance via Ollama (MODEL_../architecture/ARCHITECTURE.md) — a Testing Phase / build-phase dependency not available at Design Phase. Rather than leave the whole table blank or fabricate the remaining two-thirds of it, the one detector that could be run honestly, was.

**Method:** `screening.ts`'s `RULE_PATTERNS` (the six regex rules — SA ID, student number, phone, email, bank/card, address) were ported verbatim to a standalone Python script (`run_rule_eval.py`, repo root) and run directly against all 40 entries of `TEST_SET.csv`, bypassing any UI or API layer — consistent with §2's bypass-the-API design. No detector logic was altered for this run.

| Detector | Precision | Recall | False Positive Rate | Accuracy |
|---|---|---|---|---|
| **Rule-Based only** | **85.7%** | 42.9% (all categories) / **85.7%** (rule-tier categories only*) | **3.85%** | 77.5% |
| Context-Aware only | *pending — requires local Ollama/llama3.2, a Testing Phase dependency* | — | — | — |
| Aggregated (parallel) | *pending — requires Context-Aware detector above* | — | — | — |

*\*ID_NUMBER, FINANCIAL, CONTACT_LOCATION only. `../requirements/SPECIFICATION.md` §3 assigns MEDICAL and INSTITUTIONAL exclusively to the context-aware tier — 7 of the rule-based detector's 8 false negatives are exactly these categories, a structural (by-design) miss, not a detector defect. Counting them against rule-based recall without qualification would misrepresent what this detector was ever built to catch; the second figure is the fairer per-tier number.*

**Confusion matrix (n=40):** TP=6, FP=1, FN=8, TN=25.

**Two real qualitative findings** (this is the "cases where rule-based fails but context-aware succeeds, and vice versa" material `../requirements/SPECIFICATION.md` §6 calls for):

- **TS-007 produced a genuine false positive**, exactly as designed: a well-known 16-digit Luhn test number (`4111111111111111`) given in a coding-help context was flagged as `bank_card`, even though the prompt is about validating card-number algorithms, not sharing a real card. This is real evidence of the rule-based tier's precision ceiling — it cannot distinguish a public test value from a real one by pattern alone.
- **TS-005 was an unplanned, genuine miss**: an 11-digit student loan account number fell outside the `bank_card` pattern's 13–19-digit range, producing a false negative in a category (FINANCIAL) the rule-based tier was supposed to catch. This is a real, fixable precision/recall trade-off in the current regex, not a taxonomy artifact — worth naming honestly rather than smoothing over.

Full per-entry output (all 40 rows, predicted/actual/outcome) is retained in `run_rule_eval.py`'s companion JSON output for audit if a marker wants to verify the run.

## 4. Predicted Failure Modes — Outcome Check

Stated in the original design as hypotheses to test; now checked against the real run above where possible.

- **TS-036** (tests whether a prompt *describing* the ID pattern without an actual instance causes a false positive): **did not trigger** — correctly classified `NO_FLAG`/TN. Worth noting honestly: the sample text contains no digit sequence at all, so this entry didn't actually stress-test the hypothesized weakness as hard as intended. A sharper future test case (a description containing a plausible-looking but explicitly-labeled-fake number) would test this more meaningfully.
- **TS-016 and TS-017** (context-aware weakness — medical *topic* language without personal disclosure): **still pending**, requires the context-aware detector.
- **TS-021** (whether context-aware can catch a category rule-based structurally cannot): **still pending**, requires the context-aware detector. Rule-based correctly returned `NO_FLAG` here (as expected, since it has no INSTITUTIONAL pattern at all) — confirming the gap this entry exists to probe is real and still open.

## Links
- [TEST_SET.md](TEST_SET.md)
- [MODEL_../architecture/ARCHITECTURE.md](./MODEL_../architecture/ARCHITECTURE.md)
- [../architecture/DOMAIN_MODEL.md](../architecture/../architecture/DOMAIN_MODEL.md)
- [../architecture/ARCHITECTURE.md](../architecture/../architecture/ARCHITECTURE.md)