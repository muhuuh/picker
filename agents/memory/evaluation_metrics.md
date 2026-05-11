# Evaluation Metrics

Last updated: 2026-05-10

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
- SDK agent/tool/LLM metrics
- operational memory ids injected into agent context
- operational memory ids reported by final structured output

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
- lesson: The memory layer supports deterministic read/write/review flows, scheduled invocation, prompt-ready task context, initial SDK prompt injection, and SDK telemetry for injected/reported memory ids. Still pending: full specialist coverage, evaluating whether reported memory ids were used correctly, and feeding telemetry into reflection.
- use_when: Planning Priority 6 orchestration or Priority 7 learning-loop work.
- do_not_use_when: Treating the memory system as already fully autonomous.
- evidence: `docs/plans/investment_agent_backlog.md`, `docs/descriptions/agent_memory_workflow.md`, `stock_research/memory.py`, `stock_research/agent_runtime/tracing.py`
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

- Evaluate whether final-output reported memory ids were used correctly, not merely listed.
- Feed SDK local telemetry into post-run memory reflection.

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

- id: eval-2026-05-04-recurring-failure-command
- date: 2026-05-04
- type: evaluation
- scope: global
- status: active
- confidence: high
- trigger/source: deterministic recurring failure detection implementation
- lesson: Recurring failure detection is implemented through `python -m stock_research memory recurring-failures [--write]`. It scans memory_reflection.json artifacts across runs and proposes memory updates when issue categories recur across at least the configured threshold of distinct runs.
- use_when: Reviewing repeated run-quality problems, provider failures, missing artifacts, or recurring workflow issues across weekly/manual runs.
- do_not_use_when: Treating a single-run issue as recurring without enough reflected runs.
- evidence: `stock_research/memory_reflection.py`, `stock_research/cli.py`, `tests/test_memory_reflection.py`, `agents/memory/recurring_failures.md`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-01

- id: eval-2026-05-04-deterministic-run-finalization-is-implemented-th
- date: 2026-05-04
- type: evaluation
- scope: global
- status: active
- confidence: high
- trigger/source: deterministic run finalization implementation
- lesson: Deterministic run finalization is implemented through python -m stock_research memory finalize-run --run-id RUN_ID. It writes memory reflection artifacts, recurring failure reports, and run finalization artifacts in one command for future scheduler/orchestrator use.
- use_when: Ending a weekly/manual run, preparing scheduler integration, or reviewing whether run-learning artifacts are complete.
- do_not_use_when: Assuming memory update proposals are applied automatically or that the scheduler already invokes finalization.
- evidence: stock_research/run_finalization.py, stock_research/cli.py, tests/test_memory_reflection.py, agents/runs/2026-05-09_weekly/finalization.md
- owner: memory and evaluation orchestrator
- next_review: 2026-06-01

- id: eval-2026-05-05-bounded-memory-writer-review
- date: 2026-05-05
- type: evaluation
- scope: global
- status: active
- confidence: high
- trigger/source: bounded LLM memory writer implementation and smoke test
- lesson: Bounded memory writer review is implemented through `python -m stock_research memory writer-review --run-id RUN_ID [--execute] [--write] [--update-drafts]`. It can refine draft memory items, but it does not write operational memory directly; approved writes still go through `memory apply-updates`.
- use_when: Reviewing post-run memory update drafts, planning learning-loop orchestration, or deciding how LLM assistance may touch operational memory.
- do_not_use_when: Assuming the scheduler/orchestrator already invokes writer review automatically or bypassing deterministic schema validation.
- evidence: `stock_research/memory_llm_writer.py`, `tests/test_memory_llm_writer.py`, `docs/descriptions/llm_memory_writer.md`, `agents/runs/2026-05-09_weekly/memory_writer_review.md`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-01

- id: eval-2026-05-05-deterministic-weekly-runner
- date: 2026-05-05
- type: evaluation
- scope: orchestrator
- status: active
- confidence: high
- trigger/source: deterministic scheduled runner implementation
- lesson: `python -m stock_research run-weekly` is the deterministic weekly workflow wrapper. It reaches the framework decision boundary by chaining manifest, provider tasks, analysis tasks, run summary, quality report, memory finalization, bounded memory-writer review, and orchestration report.
- use_when: Running weekly/manual-equivalent deterministic workflow, validating the pipeline before LLM orchestration, or deciding what remains before framework selection.
- do_not_use_when: Assuming OS/app scheduling or LLM orchestrator synthesis already exists.
- evidence: `stock_research/scheduled_runner.py`, `tests/test_scheduled_runner.py`, `docs/descriptions/scheduled_runner.md`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-01

- id: eval-2026-05-10-sdk-local-telemetry
- date: 2026-05-10
- type: evaluation
- scope: orchestrator
- status: active
- confidence: high
- trigger/source: SDK local telemetry hook implementation.
- lesson: SDK `run_metrics.md` now captures agent lifecycle, tool calls, LLM calls/usage when available, injected operational memory ids, and final-output reported memory ids. Future reflection should use these metrics to find slow/brittle tools, missing memory usage, repeated tool failures, and specialist output gaps.
- use_when: Building memory/evaluation orchestration, debugging SDK runs, or deciding whether a run produced enough telemetry for learning-loop updates.
- do_not_use_when: Treating metrics as investment evidence; they describe workflow behavior only.
- evidence: `stock_research/agent_runtime/tracing.py`, `stock_research/agent_runtime/runner.py`, `tests/test_agent_runtime.py`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-15

- id: eval-2026-05-10-sdk-telemetry-reflection
- date: 2026-05-10
- type: evaluation
- scope: orchestrator
- status: active
- confidence: high
- trigger/source: Wired SDK run metrics into deterministic memory reflection.
- lesson: Post-run memory reflection should inspect `run_metrics.md` for SDK timeout/error rows, missing metrics when SDK output exists, injected memory ids, reported memory ids, tool-call counts, and LLM-call counts. These telemetry-derived issues should produce reviewable memory proposals rather than staying isolated in runtime artifacts.
- use_when: Reviewing SDK weekly/manual runs, building the memory/evaluation sub-orchestrator, or diagnosing why an SDK run ended blocked or needs_review.
- do_not_use_when: Treating telemetry as investment evidence or as a substitute for provider/company facts.
- evidence: `stock_research/memory_reflection.py`, `tests/test_memory_reflection.py`, `stock_research/agent_runtime/tracing.py`, `docs/descriptions/agent_memory_workflow.md`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-15

- id: eval-2026-05-11-runtime-quality-gate-specificity
- date: 2026-05-11
- type: evaluation
- scope: orchestrator
- status: active
- confidence: high
- trigger/source: AMZN weekly-style run exposed two over-broad SDK quality gates.
- lesson: Runtime quality gates should accept real repo artifact paths as valid proposal evidence references, not only model-returned source ids. Direct trade-language detection should look for actual stock action patterns such as `buy the stock`, `sell shares`, `trim position`, or `position size`, and should not flag ordinary business phrases such as `Sell on Amazon`.
- use_when: Updating SDK output validation, reviewing why an otherwise evidence-backed run became `needs_review`, or adding new source/citation guardrails.
- do_not_use_when: Weakening source requirements; nonexistent paths and unknown source ids should still fail validation.
- evidence: `stock_research/agent_runtime/reports.py`, `tests/test_agent_runtime.py`, `agents/runs/2026-05-16_weekly/orchestration_report.md`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-15
