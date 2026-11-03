# MODEL_ARCHITECTURE.md — Context-Aware Detector (SentryPrompt4)

**Traces to:** FR-003, FR-004, ../requirements/SPECIFICATION.md §3 (taxonomy), §6 (evaluation approach), NFR-010 (performance budget)
**Feeds:** Design Phase Template §8.3.1 (Model Architecture)

---

## 1. Model Choice

**Model:** `llama-3.1-8b-instant` on **Groq's hosted API** (default), reached through a provider interface (`backend/app/llm/`). The provider is chosen with one setting, `LLM_PROVIDER`:

| `LLM_PROVIDER` | Model (configurable) | Cost | Data use | Intended use |
|---|---|---|---|---|
| `groq` (default) | `llama-3.1-8b-instant` (`GROQ_MODEL`) | Free tier (~30 requests/min); paid ≈ US$0.03 per 1,000 checks | Terms prohibit training on API data; turn on Zero Data Retention in the Groq console | Development, evaluation, and deployment with real students |
| `gemini` | `gemini-flash-lite-latest` (`GEMINI_MODEL`) | Free tier; paid tier if billing is enabled | **Free tier may be used to improve Google's models** | Development and demos with made-up data only; refused in production unless `GEMINI_PAID_TIER=true` |
| `ollama` | `llama3.2` (`OLLAMA_MODEL`) | Free, runs locally | Never leaves the machine | Offline evaluation runs on a PC with Ollama installed |

**Why the default changed from local Ollama:** a local model meant every machine running SentryPrompt4, including a deployed server, needed Ollama installed and enough hardware to run it. A hosted free tier removes both problems and makes NFR-010's 2-second budget independent of local hardware. The cost is that screened text now leaves the machine, which REQUIREMENTS.md NFR-008 handles explicitly: rule-detected spans are redacted locally first (`backend/app/screening/redaction.py`), and only providers that do not train on API data may receive real student prompts.

**Role:** LLM-as-judge classifier — not a fine-tuned or custom-trained model. ../requirements/SPECIFICATION.md §5 explicitly rules out training a model from scratch; this is the documented, permitted alternative.

**Why an LLM-as-judge instead of a purpose-built classifier:**
- A general-purpose instruction-tuned model already has broad enough world knowledge to recognize medical and institutional-confidential language without task-specific training data — the two categories reserved for context-aware detection specifically because they resist pattern-matching (../requirements/SPECIFICATION.md §3).
- Zero-shot prompting removes the need to collect and label a large training set before the detector can function at all — the hand-labeled set built for this increment (TEST_SET.md) is for *evaluation*, not training, keeping the two concerns separate and the engineering scope solo-feasible.
- This is consistent with the feasibility argument already made in ../requirements/SPECIFICATION.md §1.3: the research contribution is the *comparison* between detection strategies, not building a custom model.

---

## 2. Classification Contract

The context-aware detector sends the **redacted** prompt text (rule-detected spans replaced with placeholders such as `[REDACTED_SA_ID]`) to the configured provider with a fixed, versioned system prompt instructing it to act strictly as a classifier and return structured JSON — not conversational text.

**System prompt (v1, stored as `backend/app/llm/prompts/context_detector_v1.txt`, versioned so evaluation runs stay comparable over time).** The design draft below is kept for reference. The implemented v1 differs in three ways: the student's text is sent as a separate user message rather than pasted into the instructions, the prompt tells the model to treat that text as data and never follow instructions inside it (prompt-injection defence), and it states that general or educational questions about health or institutional processes are *not* sensitive (aimed at the TS-016/TS-022-style false positives).

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
- **JSON mode** — every provider is called in its JSON output mode (`response_format` on Groq, `response_mime_type` on Gemini, `format: json` on Ollama), which makes parse failures rarer but not impossible.
- `temperature: 0` — deterministic output is required for reproducible evaluation runs (TC-004 depends on comparing detector outputs consistently); a non-zero temperature would make precision/recall numbers non-reproducible between runs.
- Fixed prompt template, version-controlled — so a later prompt-wording change is a visible diff, not a silent behavior change that would invalidate prior evaluation results.

**Output handling:** the Backend API parses the JSON response (`parse_classification` in `backend/app/llm/base.py`). Flags with an unknown category, or whose `span` does not appear in the text, are dropped, because they cannot be highlighted for the student (FR-005). A malformed/non-JSON response (a real risk with LLM-as-judge approaches) is treated as "no flags found" **and logged as a parse failure**, not silently dropped — this failure rate is itself worth reporting in the evaluation (Increment 13), since it's a real limitation of this approach compared to a rule-based detector, which cannot fail to parse.

---

## 3. Integration with the Existing Pipeline

No change to ../architecture/ARCHITECTURE.md's Component diagram is required — this fills in what was previously described generically as *"Pretrained NLP model or LLM-as-judge via Ollama"*. The Context-Aware Detector component now specifically means: preprocessed text → local redaction of rule-detected spans → fixed prompt template → configured LLM provider (Groq by default, temperature 0, JSON mode) → JSON parse → flagged spans passed to the Decision Aggregator, run in parallel with the Rule-Based Detector, exactly as FR-004 requires.

---

## 4. Known Limitations (stated honestly, not glossed over)

| Limitation | Why it exists | Mitigation / how it's handled |
|---|---|---|
| JSON parse failures are possible | LLM output is not guaranteed structured, even with instruction | Treated as "no flag" + logged as a parse failure, reported separately in evaluation, not hidden inside the recall number |
| Latency is not guaranteed under NFR-010's 2-second budget | Depends on the provider's response time and network conditions (and on local hardware when using Ollama) | `run_context_eval.py` records median and maximum latency per run, so this is measured rather than assumed |
| Free-tier rate limits | Groq's free tier allows about 30 requests per minute, shared across the account | Far above a capstone's load; the evaluation script paces its requests. Paid tier or another provider can be selected by configuration if needed |
| Prompts leave the machine | The default provider is a hosted API | Local redaction first, no-training providers only for real data, production guard in `factory.py` (NFR-008) |
| Confidence scores are self-reported by the model, not calibrated | LLM-as-judge confidence values are not statistically calibrated probabilities | Confidence is used for qualitative discussion (../requirements/SPECIFICATION.md §6) only, never as a hard threshold in the aggregation logic |
| Model version drift | The provider may update or retire a model between now and final submission | The model name is a configuration value, and every evaluation result file records the provider, model and prompt version used |

## Links
- [../architecture/ARCHITECTURE.md](../architecture/../architecture/ARCHITECTURE.md)
- [../requirements/REQUIREMENTS.md](../requirements/../requirements/REQUIREMENTS.md)
- [TEST_SET.md](TEST_SET.md)