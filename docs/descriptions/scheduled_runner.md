# Scheduled Runner

Last updated: 2026-05-11

## Purpose

The scheduled runner is the deterministic weekly workflow wrapper. It chains the already-built repo loaders, manifest generation, provider task runner, analysis task runner, run summary, quality report, memory finalization, and bounded memory-writer review.

Implementation: `stock_research/scheduled_runner.py`.

The runner is deterministic by default, but it can now optionally call OpenAI Agents SDK company-research fanout and the main orchestrator after deterministic finalization.

The CLI command is only the scheduler/manual entrypoint. Internal workflow steps should call importable Python functions directly rather than shelling out to other CLI commands.

## Command

Dry-run the weekly workflow without writing artifacts or calling live APIs:

```powershell
python -m stock_research run-weekly
```

Persist manifest, summaries, quality report, memory finalization, memory-writer review, and orchestration report:

```powershell
python -m stock_research run-weekly --write
```

Execute live provider and analysis tasks:

```powershell
python -m stock_research run-weekly --write --execute-providers --execute-analysis
```

When live provider or analysis execution is enabled, the runner first cleans generated artifacts in the target run directory (`evidence_packets/`, `raw/`, `reports/`, and generated root report files). This keeps repeated manual smoke tests or reruns from double-counting stale evidence packets.

Optionally call the live OpenAI-backed memory writer:

```powershell
python -m stock_research run-weekly --write --execute-memory-writer
```

Optionally call the OpenAI Agents SDK orchestrator:

```powershell
python -m stock_research run-weekly --write --execute-orchestrator
python -m stock_research run-weekly --write --execute-providers --execute-analysis --execute-orchestrator --orchestrator-timeout-seconds 300
```

`--execute-orchestrator` requires `OPENAI_API_KEY` and `--write`. SDK timeout/error results are written as blocked reviewable artifacts plus `run_metrics.md`, then memory reflection can turn them into learning-loop issues.

When SDK orchestration is enabled, the runner first runs generic company-research fanout for every ticker in `stock_tracking/current_holdings/current_holdings.csv` and `stock_tracking/monitoring/monitoring.csv`. This produces per-ticker research artifacts before the main orchestrator synthesis.

## Workflow

```text
load repo state
  -> build weekly manifest
  -> provider tasks (dry-run unless --execute-providers)
  -> analysis tasks (dry-run unless --execute-analysis)
  -> run_summary
  -> quality_report
  -> memory finalize-run
  -> memory writer-review
  -> SDK company-research fanout for current/monitoring tickers (only with --execute-orchestrator)
  -> SDK orchestrator (only with --execute-orchestrator)
  -> SDK proposal review bridge (only after successful SDK orchestrator output)
  -> final_digest
  -> human_review_digest
  -> orchestration_report
```

## Outputs

When `--write` is used:

- `agents/runs/{run_id}/manifest.json`
- `agents/runs/{run_id}/run_summary.md`
- `agents/runs/{run_id}/quality_report.md`
- `agents/runs/{run_id}/memory_reflection.md`
- `agents/runs/{run_id}/memory_update_drafts.md`
- `agents/runs/{run_id}/memory_writer_prompt.md`
- `agents/runs/{run_id}/memory_writer_review.md`
- `agents/runs/{run_id}/finalization.md`
- `agents/runs/{run_id}/final_digest.md`
- `agents/human_review_digest.md`
- `agents/runs/{run_id}/company_research/{TICKER}_company_research.md` when `--execute-orchestrator` is used and tracked tickers exist
- `agents/runs/{run_id}/company_research/{TICKER}_company_research_metrics.md` when company-research fanout writes metrics
- `agents/runs/{run_id}/agent_runtime_main_orchestrator.md` when `--execute-orchestrator` is used
- `agents/runs/{run_id}/orchestrator_update_proposals.md` when successful SDK output contains file update proposals
- `agents/runs/{run_id}/trace_links.md` when `--execute-orchestrator` is used
- `agents/runs/{run_id}/run_metrics.md` when `--execute-orchestrator` is used
- `agents/runs/{run_id}/orchestration_report.md`

Generated JSON files remain ignored local runtime artifacts.

The final digest includes readable financial formatting, explicit per-ticker evidence links, and deterministic digest quality findings when required evidence links, financial/news statuses, social-signal labels, or trade-instruction guardrails fail. The human-review digest is refreshed so the report can point the user to current approve/reject/needs-more-research/leave-open decisions.

## Status Semantics

- `dry_run`: no files were written.
- `complete`: written run completed without deterministic quality findings, provider errors, analysis errors/skips, memory finalization issues, or SDK quality/freshness findings.
- `needs_review`: provider errors, analysis errors/skips, quality findings, finalization issues, SDK errors, company-research fanout errors/partial results, SDK quality findings, or actionable SDK output from dry-run provider/analysis inputs exist.

If the SDK orchestrator is enabled while provider or analysis tasks are dry-run, it receives that execution-mode context in its prompt. If it still produces ready/actionable alerts or file update proposals, the runner appends a freshness finding and marks the scheduled run `needs_review`.

## Current Boundary

The agent framework decision is resolved:

- Selected framework: OpenAI Agents SDK.
- Dedicated plan: `docs/plans/openai_agents_sdk_orchestration_backlog.md`.
- Dedicated scratchpad: `docs/scratchpads/openai_agents_sdk_orchestration_scratchpad.md`.

Current SDK integration:

- Manual SDK run: `python -m stock_research agent-runtime run --run-id RUN_ID --execute --write`.
- Scheduled opt-in SDK run: `python -m stock_research run-weekly --write --execute-orchestrator`.
- Fresh actionable research should normally use `--execute-providers --execute-analysis --execute-orchestrator`; otherwise SDK proposals are review-only.
- Scheduled SDK orchestration now includes per-ticker company-research fanout before the main orchestrator. Fanout task names include tickers as labels only; specialists are generic and reusable.
- Repeated fresh runs are idempotent at the generated-artifact level because live execution cleans prior generated run artifacts before rebuilding them.
- Successful SDK file update proposals are routed through `orchestrator_update_proposals.md` and duplicate-safe human-review queue rows before any company-file writer can apply them.
- Approved proposals can be applied after human review with `python -m stock_research agent-runtime apply-proposal --run-id RUN_ID --proposal-id ORP-0001 --write`; this is intentionally outside the automatic weekly flow for now.
