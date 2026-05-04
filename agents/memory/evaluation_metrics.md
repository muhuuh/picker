# Evaluation Metrics

Last updated: 2026-05-04

Run-quality memory for weekly/manual runs and future post-run reflection.

## Metrics To Capture Per Run

- run_id
- run_type: weekly | manual | smoke_test
- start_time and end_time
- deterministic tasks planned
- deterministic tasks completed
- provider tasks planned/completed/failed
- analysis tasks planned/completed/failed
- evidence packets created
- quality issues found
- missing citations
- provider conflicts preserved
- false-positive alerts
- stale data fixed
- file updates made
- human review items created
- user corrections received
- memory items added/updated/deprecated

## Current Baseline

- id: eval-2026-05-03-provider-smoke-tests
- date: 2026-05-03
- type: evaluation
- scope: provider
- status: active
- confidence: high
- trigger/source: Provider implementation smoke tests.
- lesson: SEC, yfinance, Exa, xAI/Grok, FMP, Polygon/Massive, Alpha Vantage, and financial comparison have live or deterministic smoke-test artifacts. Future evaluation should treat these as baseline provider-path checks, not as investment research conclusions.
- use_when: Verifying provider regressions and planning first full weekly run.
- do_not_use_when: Making investment decisions.
- evidence: `agents/runs/2026-05-09_weekly/evidence_packets/`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-01

- id: eval-2026-05-04-learning-loop-pending
- date: 2026-05-04
- type: evaluation
- scope: global
- status: needs_review
- confidence: high
- trigger/source: User asked whether missing memory automation is recorded.
- lesson: The memory layer currently supports deterministic read, validate, summary, task-context selection, add, deprecate, post-run reflection, and memory update proposal generation. Still pending: LLM memory writer agent, orchestrator/scheduled invocation of reflection, recurring failure detection, and orchestrator injection of memory context into specialist prompts.
- use_when: Planning Priority 6 orchestration or Priority 7 learning-loop work.
- do_not_use_when: Treating the memory system as already fully autonomous.
- evidence: `docs/plans/investment_agent_backlog.md`, `docs/descriptions/agent_memory_workflow.md`, `stock_research/memory.py`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-01

## Post-Run Reflection Checklist

After a weekly or manual run:

- Which provider calls failed or produced low-value output?
- Which evidence packets lacked enough source metadata?
- Which claims were contradicted by another provider?
- Which alerts were noisy or too vague?
- Which file updates needed human correction?
- Which prompt/tool pattern worked well enough to reuse?
- Which memory item should be added, updated, superseded, or deprecated?

## Pending Automation

- LLM memory writer agent.
- Orchestrator/scheduled invocation of post-run reflection.
- Recurring failure detection.
- Orchestrator injection of task-relevant memory into specialist prompts.

## Recurring Failure Patterns

- No recurring full-run failure patterns recorded yet.
- Direct X.com API path was a corrected provider-routing mistake and is now tracked in `deprecated_memory.md` and `orchestrator_lessons.md`.

- id: eval-2026-05-04-memory-writer-commands
- date: 2026-05-04
- type: evaluation
- scope: global
- status: active
- confidence: high
- trigger/source: deterministic memory writer implementation
- lesson: Deterministic memory add and deprecate commands are implemented. Future memory writes should prefer these commands over manual Markdown edits when adding or deprecating structured memory items.
- use_when: Adding or deprecating operational memory items from Codex, future reflection steps, or future memory writer agents.
- do_not_use_when: Editing prose-only documentation or making complex memory refactors that need human review.
- evidence: `stock_research/memory.py`, `stock_research/cli.py`, `tests/test_memory.py`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-01

- id: eval-2026-05-04-reflect-run-command
- date: 2026-05-04
- type: evaluation
- scope: global
- status: active
- confidence: high
- trigger/source: deterministic post-run reflection implementation
- lesson: Deterministic post-run reflection and memory update proposal generation are implemented through `python -m stock_research memory reflect-run --run-id RUN_ID [--write]`. It writes memory_reflection.json and memory_reflection.md when requested; proposals are not applied automatically.
- use_when: Reviewing weekly/manual runs, generating memory update proposals, or planning the memory and evaluation sub-orchestrator.
- do_not_use_when: Assuming the orchestrator already invokes reflection automatically after every run.
- evidence: `stock_research/memory_reflection.py`, `stock_research/cli.py`, `tests/test_memory_reflection.py`, `agents/runs/2026-05-09_weekly/memory_reflection.md`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-01
