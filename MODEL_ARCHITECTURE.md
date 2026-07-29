# MODEL_ARCHITECTURE.md — Context-Aware Detector (SentryPrompt4)

**Traces to:** FR-003, FR-004, SPECIFICATION.md §3 (taxonomy), §6 (evaluation approach), NFR-010 (performance budget)
**Feeds:** Design Phase Template §8.3.1 (Model Architecture)

---

## 1. Model Choice

**Model:** `llama3.1` (8B, run locally via Ollama)
**Role:** LLM-as-judge classifier — not a fine-tuned or custom-trained model. SPECIFICATION.md §5 explicitly rules out training a model from scratch; this is the documented, permitted alternative.

**Why an LLM-as-judge instead of a purpose-built classifier:**
- A general-purpose instruction-tuned model already has broad enough world knowledge to recognize medical and institutional-confidential language without task-specific training data — the two categories reserved for context-aware detection specifically because they resist pattern-matching (SPECIFICATION.md §3).
- Zero-shot prompting removes the need to collect and label a large training set before the detector can function at all — the hand-labeled set built for this increment (TEST_SET.md) is for *evaluation*, not training, keeping the two concerns separate and the engineering scope solo-feasible.
- This is consistent with the feasibility argument already made in SPECIFICATION.md §1.3: the research contribution is the *comparison* between detection strategies, not building a custom model.

---

## 2. Classification Contract

The context-aware detector sends the preprocessed prompt text to `llama3.1` with a fixed, versioned system prompt instructing it to act strictly as a classifier and return structured JSON — not conversational text.

**System prompt (v1, stored as `context_detector_prompt_v1.txt` in the repo, versioned so evaluation runs stay comparable over time):**

```
You are a content classifier, not a conversational assistant. You will be given a
single piece of text. Determine whether it contains any of the following categories
of sensitive information. Respond with ONLY valid JSON, no other text.

Categories:
- MEDICAL: diagnoses, medication names, mental health disclosures, health conditions
- INSTITUTIONAL: disciplinary case details, staff performance information,
  unpublished exam or assessment content, confidential institutional records

For each category found, identify the exact substring that triggered the flag.
If no sensitive content is found, return an empty array.

Output format:
{
  "flags": [
    {"category": "MEDICAL" | "INSTITUTIONAL", "span": "<exact substring>", "confidence": <0.0-1.0>}
  ]
}

Text to classify:
"""
{prompt_text}
"""
```

**Inference parameters:**
- `temperature: 0` — deterministic output is required for reproducible evaluation runs (TC-004 depends on comparing detector outputs consistently); a non-zero temperature would make precision/recall numbers non-reproducible between runs.
- Fixed prompt template, version-controlled — so a later prompt-wording change is a visible diff, not a silent behavior change that would invalidate prior evaluation results.

**Output handling:** the Backend API parses the JSON response; a malformed/non-JSON response (a real risk with LLM-as-judge approaches) is treated as "no flags found" **and logged as a parse failure**, not silently dropped — this failure rate is itself worth reporting in the evaluation (Increment 13), since it's a real limitation of this approach compared to a rule-based detector, which cannot fail to parse.

---

## 3. Integration with the Existing Pipeline

No change to ARCHITECTURE.md's Component diagram is required — this fills in what was previously described generically as *"Pretrained NLP model or LLM-as-judge via Ollama"*. The Context-Aware Detector component now specifically means: preprocessed text → fixed prompt template → `llama3.1` inference (temperature 0) → JSON parse → flagged spans passed to the Decision Aggregator, run in parallel with the Rule-Based Detector, exactly as FR-004 requires.

---

## 4. Known Limitations (stated honestly, not glossed over)

| Limitation | Why it exists | Mitigation / how it's handled |
|---|---|---|
| JSON parse failures are possible | LLM output is not guaranteed structured, even with instruction | Treated as "no flag" + logged as a parse failure, reported separately in evaluation, not hidden inside the recall number |
| Latency is not guaranteed under NFR-010's 2-second budget | Local 8B model inference speed depends entirely on the evaluator's hardware — this was not benchmarked before model selection | Flagged here explicitly as a risk to actually measure during Increment 8's evaluation run, not assumed to pass |
| Confidence scores are self-reported by the model, not calibrated | LLM-as-judge confidence values are not statistically calibrated probabilities | Confidence is used for qualitative discussion (SPECIFICATION.md §6) only, never as a hard threshold in the aggregation logic |
| Model version drift | `llama3.1` may be updated by Ollama/Meta between now and final submission | Model tag pinned in documentation (not just "llama3.1" but a specific pulled version, to be recorded at evaluation time) |

## Links
- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [REQUIREMENTS.md](./REQUIREMENTS.md)
- [TEST_SET.md](./TEST_SET.md)
