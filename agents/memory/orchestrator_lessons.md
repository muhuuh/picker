# Orchestrator Lessons

Last updated: 2026-05-04

Operational memory for workflow routing, orchestration, run ordering, and user corrections.

## Active Lessons

- id: orch-2026-05-03-direct-x-replaced
- date: 2026-05-03
- type: procedural
- scope: orchestrator
- status: active
- confidence: high
- trigger/source: User correction during provider implementation.
- lesson: Do not implement or route to direct X.com API recent search/counts. Use xAI/Grok with built-in `x_search` via `XAI_API_KEY` for X sentiment/latest-news research.
- use_when: Planning sentiment/community research, provider tasks, or future xAI Grok specialists.
- do_not_use_when: Only change this if the user explicitly reverses the decision.
- evidence: `docs/descriptions/xai_grok_provider.md`, `stock_research/providers/xai_grok.py`, `MEMORY.md`
- owner: orchestrator
- next_review: 2026-08-01

- id: orch-2026-05-03-deterministic-first
- date: 2026-05-03
- type: procedural
- scope: orchestrator
- status: active
- confidence: high
- trigger/source: Approved architecture and implemented provider-task runner.
- lesson: Run deterministic repo loaders, provider tasks, and analysis tasks before LLM synthesis. The orchestrator should synthesize structured artifacts, not skip directly to open-ended research.
- use_when: Weekly runs, manual runs, specialist orchestration, and workflow changes.
- do_not_use_when: Tiny one-off user questions that do not need repo state or provider artifacts.
- evidence: `docs/descriptions/investment_agent_workflow.md`, `stock_research/manifest.py`, `stock_research/provider_runner.py`
- owner: orchestrator
- next_review: 2026-08-01

- id: orch-2026-05-04-financial-compare-before-specialist
- date: 2026-05-04
- type: procedural
- scope: financial
- status: active
- confidence: high
- trigger/source: Financial comparison layer implementation.
- lesson: Financial-data specialists should consume `financial_compare` evidence packets when available before making financial conclusions. Exa and Grok are excluded from this deterministic comparison by design.
- use_when: Building financial specialists, company research orchestration, and run synthesis.
- do_not_use_when: News, sentiment, or qualitative market narrative tasks.
- evidence: `docs/descriptions/financial_compare.md`, `stock_research/financial_compare.py`, `tests/test_financial_compare.py`
- owner: company research orchestrator
- next_review: 2026-08-01

- id: orch-2026-05-03-dry-run-provider-tasks
- date: 2026-05-03
- type: procedural
- scope: provider
- status: active
- confidence: high
- trigger/source: Provider task runner implementation.
- lesson: `python -m stock_research provider-tasks --manifest PATH` is dry-run by default. Live API calls require `--execute`.
- use_when: Running or documenting deterministic kickoff tasks.
- do_not_use_when: Direct provider CLI smoke tests intentionally called by the user.
- evidence: `stock_research/provider_runner.py`, `README.md`, `SETUP.md`
- owner: orchestrator
- next_review: 2026-08-01

- id: orch-2026-05-03-human-input-vs-review
- date: 2026-05-03
- type: procedural
- scope: orchestrator
- status: active
- confidence: high
- trigger/source: Human interaction layer design.
- lesson: Keep user requests and system approval requests separate. User ideas go to `docs/plans/human_research_requests.md`; system decisions requiring approval go to `agents/human_review_queue.md`.
- use_when: Routing Codex chat requests, building orchestrator approval gates, or planning manual runs.
- do_not_use_when: Purely internal provider execution with no user-facing decision.
- evidence: `docs/descriptions/human_interaction_workflow.md`, `docs/descriptions/repo_map.md`
- owner: orchestrator
- next_review: 2026-08-01

## Pending Lessons To Validate

- Whether the final agent runtime should be OpenAI Agents SDK, Pydantic AI, LangGraph, or a hybrid.
- Which provider should be the source of truth for conflicting market-data fields.
- Which file writes require human approval beyond buy/sell/position-size recommendations and stock status moves.
- How the orchestrator will inject task-relevant operational memory into each specialist prompt.
- How the memory and evaluation sub-orchestrator will coordinate automatic post-run reflection, memory update proposals, and the LLM memory writer agent.

- id: orch-2026-05-04-analysis-tasks-can-now-be-dry-run-or-executed-fr
- date: 2026-05-04
- type: procedural
- scope: orchestrator
- status: active
- confidence: high
- trigger/source: deterministic analysis task runner implementation
- lesson: Analysis tasks can now be dry-run or executed from manifests through python -m stock_research analysis-tasks --manifest PATH [--execute]. Run provider tasks first, then analysis tasks, then run summary/quality report/finalization.
- use_when: Running weekly/manual deterministic workflows, scheduler integration, or orchestrator kickoff planning.
- do_not_use_when: Executing live provider API calls; use provider-tasks for provider work.
- evidence: stock_research/analysis_runner.py, stock_research/cli.py, tests/test_analysis_runner.py, docs/descriptions/analysis_task_runner.md
- owner: main orchestrator
- next_review: 2026-06-01
