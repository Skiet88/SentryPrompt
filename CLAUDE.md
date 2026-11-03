# CLAUDE.md

## Working preferences
- Default to discussion and planning. When I describe what we will do,
  explain and recommend; don't implement it until I explicitly say so.
- Always ask before: writing or changing files, installing packages or SDKs,
  running tests, committing, pushing, or opening pull requests.
- When unsure whether I'm asking for action or just talking it through, ask.

## Design rules (apply to every file)
- Follow SOLID: one responsibility per class/module; extend by adding
  classes, not by editing existing ones; depend on interfaces, not
  concrete classes; keep interfaces small.
- Layered packages: domain, factory, util, repository, service, screening,
  llm, api, schemas, config, exception. Each layer only calls the layer
  below it through an interface.
- Entities are immutable and created only through their factory, which
  validates input.
- Use the established patterns: Factory, Repository, Service, Strategy
  (detectors, LLM providers), Facade (screening pipeline), dependency
  injection wired in main.py.
- Tests mirror the app packages; every factory, service and router has tests.

## Security rules
These standing security rules apply to every change:

@SECURITY_RULES.md
