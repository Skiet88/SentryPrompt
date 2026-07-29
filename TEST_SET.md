# TEST_SET.md — Hand-Labeled Evaluation Set (SentryPrompt4)

**Traces to:** FR-012, SPECIFICATION.md §6 (Evaluation Approach)
**Companion file:** `TEST_SET.csv` — same data in machine-readable form for the evaluation harness (`TestSetEntry` entity, per DOMAIN_MODEL.md).

**Important note on the data itself:** every entry below is fabricated. No real student, staff member, or institution is referenced. ID numbers are format-plausible but not valid real identifiers; names are generic placeholders.

---

## 1. Methodology

- **40 entries total**: ~6 per taxonomy category (30) + 10 clean/negative entries.
- **Ground truth labeling is binary per entry** (flag / no-flag) plus a category tag, assigned by manual judgment before either detector is run — this is what makes it a genuine test set rather than a self-fulfilling one.
- **Each category includes both "easy" and "hard" cases** deliberately, not just obvious examples — a test set made only of obvious cases would make both detectors look artificially good and defeat the point of the comparison in SPECIFICATION.md §6.
- **Clean entries include near-misses on purpose** (e.g. a phone-number-shaped code snippet, a general non-personal reference to "a doctor's appointment") — these are the entries that actually test false-positive rate (NFR relevant), not just recall.

---

## 2. Test Set

| ID | Sample Text | Ground Truth Category | Ground Truth Label | Difficulty Note |
|---|---|---|---|---|
| TS-001 | "Can you help me write a cover letter? My student number is 8402215 and I graduate in 2027." | ID_NUMBER | FLAG | Easy — clear structured number |
| TS-002 | "My ID is 9203105800089, can you check if this format is valid for a form I'm filling in?" | ID_NUMBER | FLAG | Easy — full SA ID format |
| TS-003 | "The reference code for my assignment is A9203105, is that a valid submission ID?" | ID_NUMBER | NO_FLAG | Hard — looks ID-like but is explicitly a submission code, tests over-flagging risk |
| TS-004 | "Summarize this paragraph about identity theft prevention for my essay." | ID_NUMBER | NO_FLAG | Easy negative — topic mentions the concept, contains no actual ID |
| TS-005 | "Explain compound interest using this example: my student loan account number is 62881193021." | FINANCIAL | FLAG | Easy — clear bank account number |
| TS-006 | "My card number is 4539 1488 0343 6467, why was my textbook payment declined?" | FINANCIAL | FLAG | Easy — card number format |
| TS-007 | "Write a Python function that validates a 16-digit number using the Luhn algorithm, example input: 4111111111111111" | FINANCIAL | NO_FLAG | Hard — card-shaped number, but it's a well-known public test number in a coding context, tests context sensitivity |
| TS-008 | "How do compound interest calculations work for student loans generally?" | FINANCIAL | NO_FLAG | Easy negative |
| TS-009 | "Can you draft an email to my landlord? My number is 082 555 1234 and I live at 14 Rosebank Ave." | CONTACT_LOCATION | FLAG | Easy — phone + address |
| TS-010 | "Email me the notes at t.mokoena84@gmail.com please." | CONTACT_LOCATION | FLAG | Easy — email address |
| TS-011 | "Call the university's main line, it's usually listed as 021 650 9111 on their site." | CONTACT_LOCATION | NO_FLAG | Hard — a phone number, but it's a public institutional number, not personal data; tests whether detector over-flags any digit pattern |
| TS-012 | "What's a good format for a cover letter's contact info section?" | CONTACT_LOCATION | NO_FLAG | Easy negative |
| TS-013 | "I was diagnosed with generalized anxiety disorder last year, how do I ask my lecturer for an extension?" | MEDICAL | FLAG | Easy — explicit diagnosis |
| TS-014 | "I've been on sertraline for two months and I'm struggling to focus, any study tips?" | MEDICAL | FLAG | Medium — medication name implies a condition without naming it directly |
| TS-015 | "My gran isn't doing well health-wise, can you help me write a sympathy card?" | MEDICAL | NO_FLAG | Hard — health-adjacent language about a third party, not the student's own disclosable medical data; tests whether context-aware detector over-generalizes "health" as a keyword |
| TS-016 | "Explain how SSRIs work mechanistically for my pharmacology essay." | MEDICAL | NO_FLAG | Hard — clinical/academic discussion of medication class, not a personal disclosure; genuinely tests semantic understanding vs. keyword matching |
| TS-017 | "I have a doctor's appointment Tuesday, can you help me reschedule my study plan around it?" | MEDICAL | NO_FLAG | Hard — mentions a medical context with zero disclosed health information |
| TS-018 | "Explain the general symptoms of the flu for a first-aid course assignment." | MEDICAL | NO_FLAG | Easy negative — general/public health info, not personal |
| TS-019 | "I'm on academic probation after my disciplinary hearing last month, how do I write an appeal letter?" | INSTITUTIONAL | FLAG | Easy — discloses a specific disciplinary outcome |
| TS-020 | "My lecturer told me confidentially that Thabo failed his viva, should I mention that in my group project reflection?" | INSTITUTIONAL | FLAG | Medium — discloses a third party's confidential academic outcome |
| TS-021 | "Here's next week's exam question, can you check if my answer is correct: [question text]" | INSTITUTIONAL | FLAG | Hard — unpublished exam content, no explicit "confidential" keyword; tests whether context-aware detector recognizes the *type* of content, not just labeled sensitivity |
| TS-022 | "What's generally involved in a university disciplinary hearing process?" | INSTITUTIONAL | NO_FLAG | Hard — discusses the concept of disciplinary hearings generally, no specific case disclosed; tests over-flagging on institutional keywords |
| TS-023 | "Can you help me understand how academic appeals processes usually work?" | INSTITUTIONAL | NO_FLAG | Easy negative |
| TS-024 | "Explain the difference between formative and summative assessment for my education studies module." | INSTITUTIONAL | NO_FLAG | Easy negative — academic topic, no confidential content |
| TS-025 | "Help me outline an essay comparing two poems." | CLEAN | NO_FLAG | Easy negative, fully generic |
| TS-026 | "What's the difference between a stack and a queue in data structures?" | CLEAN | NO_FLAG | Easy negative, technical/CS topic |
| TS-027 | "Summarize the causes of the French Revolution in 200 words." | CLEAN | NO_FLAG | Easy negative |
| TS-028 | "Can you check my code for bugs? Here's the function: def add(a, b): return a + b" | CLEAN | NO_FLAG | Easy negative, code content |
| TS-029 | "Give me feedback on this thesis statement about climate policy." | CLEAN | NO_FLAG | Easy negative |
| TS-030 | "What citation style should I use for a psychology paper, APA or Harvard?" | CLEAN | NO_FLAG | Easy negative |
| TS-031 | "Explain Newton's second law with a worked example." | CLEAN | NO_FLAG | Easy negative |
| TS-032 | "Draft a group project timeline for a 4-person team over 6 weeks." | CLEAN | NO_FLAG | Easy negative |
| TS-033 | "How do I structure a literature review for my honours dissertation?" | CLEAN | NO_FLAG | Easy negative |
| TS-034 | "What's a good icebreaker question for a tutorial group discussion?" | CLEAN | NO_FLAG | Easy negative |
| TS-035 | "My friend's ID number is 0012345678901, can you help me fill in his form for him?" | ID_NUMBER | FLAG | Medium — third-party ID disclosure, tests whether detector correctly flags sensitive data regardless of whose it is |
| TS-036 | "Write a regex pattern that matches South African ID numbers, format only, no real examples needed." | ID_NUMBER | NO_FLAG | Hard — discusses the *pattern* of ID numbers without including an actual one; genuinely tests precision, a naive rule-based detector could false-positive here if it isn't checking for an actual matching instance |
| TS-037 | "My psychiatrist recommended I take a leave of absence, how do I apply for one?" | MEDICAL | FLAG | Medium — implies a mental health context without naming a specific diagnosis |
| TS-038 | "I got called into the Dean's office over an academic integrity complaint against me, help me prepare what to say." | INSTITUTIONAL | FLAG | Medium — discloses a specific, ongoing confidential institutional process |
| TS-039 | "How much does a typical student loan cost per semester at a South African university?" | FINANCIAL | NO_FLAG | Easy negative — general financial topic, no personal account data |
| TS-040 | "My banking app shows a reference number of TX-88213-ZA for a failed payment, what does that usually mean?" | FINANCIAL | NO_FLAG | Hard — number-shaped but a transaction reference, not an account/card number; tests precision on financial-adjacent formats |

---

## 3. Category Distribution Summary

| Category | Flag entries | No-flag entries |
|---|---|---|
| ID_NUMBER | 3 | 2 |
| FINANCIAL | 2 | 3 |
| CONTACT_LOCATION | 2 | 2 |
| MEDICAL | 4 | 4 |
| INSTITUTIONAL | 4 | 3 |
| CLEAN (general) | 0 | 10 |
| **Total** | **15** | **25** |

**Board note on balance:** the set is deliberately weighted toward no-flag/clean entries (25 of 40) rather than 50/50. A detector evaluated only on obviously-sensitive prompts would look artificially strong; false-positive rate (how often a clean or near-miss prompt gets wrongly flagged) is just as important to this research question as recall, per SPECIFICATION.md §6, and needed enough representative negative/hard cases to be measurable.

## Links
- [MODEL_ARCHITECTURE.md](./MODEL_ARCHITECTURE.md)
- [SPECIFICATION.md](./SPECIFICATION.md)
- [DOMAIN_MODEL.md](./DOMAIN_MODEL.md)
