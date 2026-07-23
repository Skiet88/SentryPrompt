# SentryPrompt4

**Context-Aware NLP Screening for Sensitive Information in Higher Education AI Prompts**

## Introduction

SentryPrompt4 is a research prototype that screens student-authored prompts for sensitive personal and institutional information *before* they reach an AI model. Students increasingly use tools like ChatGPT, Claude, and Gemini for academic work, often without realizing they've included personal identifiers, medical details, or confidential institutional data in a prompt. Under South Africa's POPIA legislation, this creates real legal exposure — and no lightweight, student-facing tool currently exists to prevent it.

SentryPrompt4 sits between the student and the AI model, the way a browser sits between a user and the internet: it does not replace the model, it mediates access to it. It screens each prompt using a combination of rule-based pattern detection and a context-aware NLP method, warns the student when something sensitive is detected, explains why, and lets the student decide how to proceed — edit, send anyway, or cancel.

Once complete, this project will provide:
- A working chat web application with built-in prompt screening, connected to a local Ollama model
- A companion browser extension that screens prompts typed into existing AI platforms, without requiring students to abandon their preferred tools
- A research comparison between rule-based and context-aware detection methods, evaluated on precision, recall, and false-positive rate

## Documentation

- [SPECIFICATION.md](./SPECIFICATION.md) — full problem statement, domain, scope, sensitive-information taxonomy, and evaluation approach
- [ARCHITECTURE.md](./ARCHITECTURE.md) — C4 architectural diagrams (Context, Container, Component) covering all end-to-end system components

## Status

🚧 In active development
