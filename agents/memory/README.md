# Agent Memory

Operational memory for the stock research agents.

This folder stores lessons that help future Codex chats, orchestrators, and specialist agents perform better. It is not a place for investment facts.

Investment facts belong in:

- `stock_tracking/stock_info_files/`
- `stock_tracking/*/*_state.md`
- `strategy/`
- `agents/runs/*/evidence_packets/`
- `MEMORY.md` for durable repo-level decisions

## Start Here

Read `memory_index.md` first. It tells each task which memory files are relevant.

## Memory Surfaces

- `orchestrator_lessons.md`: orchestration, routing, and workflow lessons.
- `source_quality.md`: provider/source reliability and known gotchas.
- `specialist_playbooks.md`: procedural memory for specialist agents.
- `evaluation_metrics.md`: run-quality metrics and recurring failure patterns.
- `deprecated_memory.md`: superseded or wrong lessons that must not be reintroduced.

## Memory Item Shape

Use this structure for important entries:

```text
- id:
- date:
- type: semantic | episodic | procedural | source_quality | evaluation
- scope: orchestrator | provider | financial | news | sentiment | writer | global
- status: active | superseded | deprecated | needs_review
- confidence: low | medium | high
- trigger/source:
- lesson:
- use_when:
- do_not_use_when:
- evidence:
- owner:
- next_review:
```

## Write Rules

- Keep entries short, actionable, and evidence-backed.
- Link to evidence packets, traces, docs, or user corrections.
- Do not store raw provider output here.
- Do not store API keys, tokens, private account data, or broker data.
- Do not store company facts unless the lesson is about source reliability or workflow behavior.
- Update an existing memory when possible instead of duplicating it.
- If a memory is wrong, mark it superseded or move the lesson to `deprecated_memory.md`.
