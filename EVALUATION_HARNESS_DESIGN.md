# EVALUATION_HARNESS_DESIGN.md — SentryPrompt4

**Traces to:** FR-012, UC8 (Run Evaluation Against Test Set), the Increment 2A architecture gap (offline entry point into the Screening Service)
**Feeds:** Design Phase Template §8.3.2 (Data Pipeline validation), real numbers for §9

---

## 1. Purpose

This is the design for the script that answers SentryPrompt4's actual research question: does parallel rule-based + context-aware detection outperform either method alone? It runs `TEST_SET.csv` through both detectors **independently**, compares each to ground truth, and computes the metrics SPECIFICATION.md §6 commits to.

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
   research discussion material for SPECIFICATION.md §6 ("cases where rule-based fails but
   context-aware succeeds, and vice versa")
```

**Why this bypasses the API/UI layer entirely (per Increment 2A):** the harness calls the Screening Service's detectors directly — the same code path the Backend API would call, but invoked from a script, not a live student request. This is what makes UC8 genuinely "independent of live usage" rather than requiring a running web session for every evaluation run.

## 3. Expected Output Format

| Detector | Precision | Recall | False Positive Rate |
|---|---|---|---|
| Rule-Based only | *(computed at run time)* | *(computed at run time)* | *(computed at run time)* |
| Context-Aware only | *(computed at run time)* | *(computed at run time)* | *(computed at run time)* |
| Aggregated (parallel) | *(computed at run time)* | *(computed at run time)* | *(computed at run time)* |

**Board note — this table is deliberately left uncomputed here.** Filling in numbers now, before either detector is actually built and run, would mean fabricating research results — the same fabrication risk flagged in TEST_CASES.md. This table gets populated once the detectors exist and TEST_SET.csv is actually run through them, and that run is what belongs in the Design Phase Template's evaluation section, not a placeholder invented at design time.

## 4. Predicted Failure Modes (hypotheses to test, not claims)

Stated here as things to specifically watch for when the real run happens, since a few entries in TEST_SET.md were deliberately designed to probe them:

- **TS-036 tests a known rule-based weakness:** a prompt *describing* the ID number pattern without containing an actual instance. A naive regex-only detector risks a false positive here if it matches on structure without confirming full context.
- **TS-016 and TS-017 test a known context-aware weakness:** medical *topic* language without personal disclosure. If the context-aware detector over-flags these, that's evidence it's pattern-matching on keywords ("SSRI," "doctor's appointment") rather than genuinely detecting disclosure, which would be a meaningful finding for the qualitative discussion.
- **TS-021 tests whether context-aware detection can catch a category rule-based detection structurally cannot** (unpublished exam content has no fixed pattern) — this entry is the clearest single test of the entire research question.

## Links
- [TEST_SET.md](./TEST_SET.md)
- [MODEL_ARCHITECTURE.md](./MODEL_ARCHITECTURE.md)
- [DOMAIN_MODEL.md](./DOMAIN_MODEL.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
