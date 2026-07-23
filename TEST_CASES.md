# TEST_CASES.md — SentryPrompt4

**Traceability:** Each test case validates a specific FR/NFR from REQUIREMENTS.md and a use case from USE_CASES.md. This document defines *what* will be tested; Actual Result / Status columns are intentionally left pending until implementation exists (see Board Review Notes).

**Revision note:** an audit against all 12 functional requirements found that FR-001, FR-006, and FR-009 had no corresponding test case in the prior draft — a coverage gap that a "bulletproof" claim cannot tolerate. TC-011, TC-012, and TC-013 close that gap below. A coverage matrix (§3) is now included so a gap like this cannot recur silently.

---

## 1. Functional Test Cases

| Test Case ID | Requirement ID | Description | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| TC-001 | FR-002 | Rule-based detector catches a South African ID number | 1. Submit prompt containing a valid-format 13-digit SA ID number. 2. Observe classification. | Prompt is flagged; ID number span is highlighted. | *pending* | *pending* |
| TC-002 | FR-002 | Rule-based detector catches an email address | 1. Submit prompt containing a plausible email address. 2. Observe classification. | Prompt is flagged; email span is highlighted. | *pending* | *pending* |
| TC-003 | FR-003 | Context-aware detector catches a medical disclosure with no structured pattern | 1. Submit prompt describing a diagnosis in plain language, no ID/number present. 2. Observe classification. | Prompt is flagged by context-aware detector even though rule-based detector finds nothing. | *pending* | *pending* |
| TC-004 | FR-004 | Both detectors run independently on the same prompt | 1. Submit a prompt containing both a phone number and a medical disclosure. 2. Inspect the log entry for this submission. | Log shows both detectors returned independent results for the same prompt, not a short-circuited fallback. | *pending* | *pending* |
| TC-005 | FR-005 | Flagged span highlighting is specific, not generic | 1. Submit a prompt with one sensitive phrase embedded in otherwise clean text. 2. Observe UI. | Only the sensitive phrase is highlighted, not the entire prompt. | *pending* | *pending* |
| TC-006 | FR-007 | All three flagged-prompt actions are available and functional | 1. Trigger a flag. 2. Confirm Edit, Send Anyway, and Cancel are all present and clickable. | All three actions available; each produces its documented outcome. | *pending* | *pending* |
| TC-007 | FR-008 | Cancelled flagged prompt never reaches Ollama | 1. Trigger a flag. 2. Select Cancel. 3. Inspect Backend API / Ollama request logs. | No request to Ollama is made for the cancelled prompt. | *pending* | *pending* |
| TC-008 | FR-010 | Extension screens a prompt on a live third-party platform page before native submission | 1. Open a supported third-party AI platform with extension active. 2. Type a flaggable prompt into its native input. 3. Attempt to send. | Extension intercepts before native send fires; review flow (UC3) triggers first. | *pending* | *pending* |
| TC-009 | FR-011 | Log entries exclude raw sensitive content | 1. Submit and flag a prompt containing sensitive content. 2. Inspect the resulting log entry directly. | Log entry contains classification/category/metadata only — no raw sensitive substring present. | *pending* | *pending* |
| TC-010 | FR-012 | Evaluation script runs independent of live student session | 1. Run the evaluation harness against the labeled test set with no web app/extension session active. 2. Confirm it completes and produces metrics. | Precision/recall/false-positive metrics are produced without requiring a live UI interaction. | *pending* | *pending* |
| TC-011 | FR-001 | System rejects empty prompt input without running detection | 1. Submit an empty (or whitespace-only) prompt via the web app. 2. Observe system response. | A clear validation message is shown; no detection cycle is triggered; nothing is logged as a screening event. | *pending* | *pending* |
| TC-012 | FR-006 | Flagged explanation is plain-language and names the correct category | 1. Trigger a flag for a known category (e.g. medical disclosure). 2. Read the displayed explanation text. | Explanation names the specific category detected (not a generic "flagged" message) and avoids technical/legal jargon. | *pending* | *pending* |
| TC-013 | FR-009 | AI response is returned via the same interface the prompt originated from | 1. Submit an approved prompt via the web app. 2. Separately, submit one via the extension on a third-party platform. 3. Observe where each response appears. | Web app prompt's response appears in the web app; extension-originated prompt's response appears in the third-party platform's own interface. | *pending* | *pending* |

---

## 2. Non-Functional Test Scenarios

| Test Case ID | Requirement ID | Description | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| TC-NF-001 | NFR-010 (Performance) | Combined screening completes within 2 seconds for a typical prompt | 1. Submit a ~150-word prompt. 2. Measure time from submission to classification result being returned. | Result returned within 2 seconds on standard development hardware. | *pending* | *pending* |
| TC-NF-002 | NFR-008 (Security) | No prompt content leaves the local machine during SentryPrompt4's own screening/inference | 1. Submit a prompt via the web app (not the extension). 2. Monitor outbound network traffic during the request. 3. Confirm all traffic is to localhost/local Ollama only. | No outbound traffic to any non-local address occurs for the screening and web-app-response flow. Extension flow (UC2) is explicitly out of scope for this test, per the corrected NFR-008 wording. | *pending* | *pending* |

---

## 3. Requirement Coverage Matrix

A test suite claiming to be complete has to prove it, not just assert it. This table confirms every FR and every NFR has at least one test case; anything without one is a gap, not an assumption.

| Requirement | Covered by |
|---|---|
| FR-001 | TC-011 |
| FR-002 | TC-001, TC-002 |
| FR-003 | TC-003 |
| FR-004 | TC-004 |
| FR-005 | TC-005 |
| FR-006 | TC-012 |
| FR-007 | TC-006 |
| FR-008 | TC-007 |
| FR-009 | TC-013 |
| FR-010 | TC-008 |
| FR-011 | TC-009 |
| FR-012 | TC-010 |
| NFR-008 (Security) | TC-NF-002 |
| NFR-010 (Performance) | TC-NF-001 |

**Requirements with no dedicated test case (by deliberate decision, stated not hidden):** NFR-001–NFR-002 (Usability), NFR-003–NFR-004 (Deployability), NFR-005–NFR-006 (Maintainability), NFR-007 (Scalability), NFR-009 (Security — partially covered indirectly by TC-009's log-content check, but not a dedicated scenario). These are qualitative/structural requirements better verified by design review and code inspection than by a discrete test case, and are tracked instead in the Evaluation of Design section (Increment 13), not silently dropped.

---

## 4. Board Review Notes

- **Why "Actual Result" and "Status" are left pending:** filling these in now, before any code exists, would mean fabricating test results — a fabrication risk this board explicitly guards against. These columns are completed during/after implementation, not during design.
- **TC-NF-002 scope note:** written narrowly on purpose. Testing "no external transmission" broadly would contradict the extension's actual function (UC2 legitimately sends approved prompts to third-party platforms). The test is scoped to validate only the part of NFR-008 that's a hard constraint — the screening/inference path.
- **Gap acknowledged, not silently missing:** no load/concurrency test exists, since NFR-007 (scalability) explicitly targets single-user local load for this prototype. Adding one here would test something outside the stated scope.

## Links
- [USE_CASES.md](./USE_CASES.md)
- [REQUIREMENTS.md](./REQUIREMENTS.md)
