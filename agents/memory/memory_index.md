# Agent Memory Index

Last updated: 2026-05-11

## Purpose

This is the entry point for operational agent memory. Future Codex chats, orchestrators, and specialists should read this file before loading deeper memory.

## What To Read

| Task | Required memory |
| --- | --- |
| Any orchestration, manifest, or workflow task | `orchestrator_lessons.md` |
| Any provider, source, citation, or evidence task | `source_quality.md` |
| Any specialist-agent design or implementation task | `specialist_playbooks.md` |
| Any quality review, run summary, or learning-loop task | `evaluation_metrics.md`, `source_quality.md` |
| Any memory/evaluation sub-orchestrator task | `evaluation_metrics.md`, `orchestrator_lessons.md`, `source_quality.md` |
| Any human-review, approval, notification, or portfolio-review task | `orchestrator_lessons.md`, `specialist_playbooks.md` |
| Any change that reverses old behavior | `deprecated_memory.md` |
| Any file-writing specialist task | `specialist_playbooks.md`, relevant repo docs |

## Load Order

At task start:

1. Read `MEMORY.md`.
2. Read `docs/descriptions/repo_map.md`.
3. Read the relevant scratchpad in `docs/scratchpads/`.
4. Read this file.
5. Read only the task-relevant memory files listed above.

## Memory Boundaries

- `MEMORY.md`: durable repo decisions and high-impact user decisions.
- `docs/scratchpads/`: short topic memory and current work state.
- `agents/memory/`: operational lessons for agent performance, source reliability, procedures, and evaluation.
- `agents/runs/`: raw run artifacts, evidence packets, summaries, quality reports, and traces.
- `stock_tracking/`, `market_research/`, `strategy/`: investment facts, state, and strategy.

## Write Paths

- Hot-path writes: use immediately for high-impact user corrections or dangerous repeated mistakes.
- Post-run reflection: after weekly/manual runs, extract useful lessons from provider failures, quality reports, user corrections, and run summaries.
- Human review: when a memory change would alter strategy, approval rules, or high-impact workflow behavior, add an item to `agents/human_review_queue.md`.

## Future JSON Item Store

If these Markdown files become too large, add structured items under:

```text
agents/memory/items/YYYY-MM-DD_memory-id.json
```

Do not add a vector database until the Markdown memory is too large for reliable manual and Codex review.
