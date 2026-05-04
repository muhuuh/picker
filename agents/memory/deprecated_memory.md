# Deprecated Memory

Last updated: 2026-05-04

Superseded or wrong operational lessons. Keep this file so future agents do not accidentally reintroduce corrected behavior.

## Deprecated Lessons

- id: deprecated-2026-05-03-direct-x-api
- date: 2026-05-03
- type: procedural
- scope: sentiment
- status: deprecated
- confidence: high
- trigger/source: User correction.
- lesson: Direct X.com API recent search/counts with bearer-token auth was the wrong path for this repo.
- replacement: Use xAI/Grok with built-in `x_search` via `XAI_API_KEY` for X sentiment/latest-news research.
- use_when: Checking whether a proposed X/social implementation is valid.
- do_not_use_when: Do not revive direct X.com API unless the user explicitly reverses the decision.
- evidence: `docs/descriptions/xai_grok_provider.md`, `stock_research/providers/xai_grok.py`, `agents/memory/orchestrator_lessons.md`
- owner: orchestrator
- next_review: 2026-08-01
