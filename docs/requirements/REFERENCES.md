# REFERENCES.md — SentryPrompt4

**Feeds:** Design Phase Template §11 (References) — minimum 5 academic/industry sources, Harvard style
**Source:** every reference below is carried directly from the approved Research Methods Assignment 1 proposal (Mbuyazi, M., "Context-Aware NLP Models for Detecting and Mitigating Sensitive Information in Higher Education AI Prompts"). Nothing here is invented or added at the design phase — this document only formats what the research proposal already established as this project's grounding literature.

---

Bloomberg. (2023). *Samsung bans ChatGPT, Google Bard, other generative AI use by staff after leak.* Bloomberg Technology. Available at: https://www.bloomberg.com/news/articles/2023-05-02/samsung-bans-chatgpt-and-other-generative-ai-use-by-staff-after-leak [Accessed: date of access].

Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J., Dhariwal, P. and Amodei, D. (2020). Language models are few-shot learners. *Advances in Neural Information Processing Systems*, 33, pp.1877–1901.

Chen, Y., Liu, Y. and Wang, H. (2025). Preempt: Sanitizing sensitive prompts for large language models. *arXiv preprint*, arXiv:2504.05147.

Contextual AI Lab. (2025). Towards contextual sensitive data detection. *arXiv preprint*, arXiv:2512.04120.

Council on Higher Education. (2016). *South African higher education reviewed: Two decades of democracy.* Pretoria: Council on Higher Education.

Dey, A.K. (2001). Understanding and using context. *Personal and Ubiquitous Computing*, 5(1), pp.4–7.

European Parliament and Council of the European Union. (2016). Regulation (EU) 2016/679 of the European Parliament and of the Council of 27 April 2016 on the protection of natural persons with regard to the processing of personal data. *Official Journal of the European Union*, L119, pp.1–88.

Gupta, R., Patel, S. and Nair, V. (2024). Adaptive PII mitigation framework for large language models. *arXiv preprint*, arXiv:2501.12465.

Jurafsky, D. and Martin, J.H. (2023). *Speech and language processing.* 3rd ed. Upper Saddle River: Prentice Hall.

Kim, J., Park, S. and Lee, H. (2024). Trust no bot: Discovering personal disclosures in human-LLM conversations in the wild. *arXiv preprint*, arXiv:2407.11438.

Lee, C., Zhang, W. and Huang, X. (2024). Privacy- and bias-aware NLP using named entity recognition. *arXiv preprint*, arXiv:2507.02966.

Mireshghallah, F., Uniyal, A., Wang, T., Evans, D. and Berg-Kirkpatrick, T. (2024). Casper: Prompt sanitization for protecting user privacy in web-based large language models. *arXiv preprint*, arXiv:2408.07004.

National Institute of Standards and Technology (NIST). (2010). *Guide to protecting the confidentiality of personally identifiable information (PII).* NIST Special Publication 800-122. Gaithersburg: NIST.

Oxford English Dictionary. (2024). Mitigation. Oxford: Oxford University Press. Available at: https://www.oed.com [Accessed 15 March 2026].

Republic of South Africa. (2013). *Protection of Personal Information Act 4 of 2013.* Pretoria: Government Printer.

Roos, A. (2024). The regulation of artificial intelligence through data protection laws: Insights from South Africa. *African Journal of Privacy and Data Protection*, 1(1), pp.1–22.

Russell, S. and Norvig, P. (2021). *Artificial intelligence: A modern approach.* 4th ed. Upper Saddle River: Pearson.

Sharma, R., Das, A. and Gupta, P. (2024). Detecting contextually sensitive data with AI. *Journal of Data Privacy and Security*, 12(3), pp.45–67.

Shi, W., Ajith, A., Xia, M., Huang, Y., Liu, D., Blevins, T., Chen, D. and Zettlemoyer, L. (2024). Detecting pretraining data from large language models. *arXiv preprint*, arXiv:2111.09509.

Yan, L., Zhao, L. and Gasevic, D. (2024). Ethics of artificial intelligence in education: Student privacy and data protection. *Science Insights Education Frontiers*, 16(2), pp.1–18.

Zhang, T., Li, Q. and Zhou, M. (2024). The challenges and countermeasures of ChatGPT-type generative artificial intelligence on information subjects' right to know. *AI and Ethics*, 4(2), pp.311–325.

---

## Where each source is actually used in this project

Stated explicitly so this reference list reads as grounding the design, not as a bolted-on citation dump satisfying a rubric line item:

| Source | Used in |
|---|---|
| Kim, Park and Lee (2024) — 70% PII-in-conversations finding | SPECIFICATION.md §1.2 — the core motivating statistic |
| Bloomberg (2023) — Samsung ChatGPT leak | SPECIFICATION.md §1.2 — the real-world incident grounding the problem |
| Republic of South Africa (2013) — POPIA | SPECIFICATION.md §1.2; REQUIREMENTS.md NFR-011, NFR-014; the project's entire legal framing |
| Roos (2024) | SPECIFICATION.md §1.2 — the regulatory-gap argument (no technical standard exists yet) |
| Mireshghallah et al. (2024) — Casper | SPECIFICATION.md §1.2 — the closest prior work, and the reason this project targets students specifically, not enterprise DLP |
| Chen et al. (2025) — Preempt | SPECIFICATION.md §1.2 — same role as above, encryption/differential-privacy angle |
| Sharma, Das and Gupta (2024); Contextual AI Lab (2025) | SPECIFICATION.md §1.2 — the justification for including a context-aware detector at all, not just rule-based pattern matching |
| NIST (2010) | Informs the five-category sensitive-information taxonomy in SPECIFICATION.md §3 |

**Note on remaining sources:** Brown et al. (2020), Jurafsky and Martin (2023), Russell and Norvig (2021), Dey (2001), and the EU GDPR regulation (2016) are foundational NLP/AI/context-computing/data-protection references from the original proposal's literature review — they ground the discipline this project sits within, even where they are not cited against a specific design decision above.

## Links
- [SPECIFICATION.md](SPECIFICATION.md)
- [MODEL_../architecture/ARCHITECTURE.md](./MODEL_../architecture/ARCHITECTURE.md)
- [PROJECT_BACKLOG.md](PROJECT_BACKLOG.md)
