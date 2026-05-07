# Scheduled Runner

Last updated: 2026-05-06

## Purpose

The scheduled runner is the deterministic weekly workflow wrapper. It chains the already-built repo loaders, manifest generation, provider task runner, analysis task runner, run summary, quality report, memory finalization, and bounded memory-writer review.

Implementation: `stock_research/scheduled_runner.py`.

The runner is deterministic by default, but it can now optionally call the OpenAI Agents SDK main orchestrator after deterministic finalization.

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
python -m stock_research run-weekly --write --execute-providers --execute-analysis --execute-orchestrator
```

`--execute-orchestrator` requires `OPENAI_API_KEY` and `--write`.

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
  -> SDK orchestrator (only with --execute-orchestrator)
  -> SDK proposal review bridge (only after successful SDK orchestrator output)
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
- `agents/runs/{run_id}/agent_runtime_main_orchestrator.md` when `--execute-orchestrator` is used
- `agents/runs/{run_id}/orchestrator_update_proposals.md` when successful SDK output contains file update proposals
- `agents/runs/{run_id}/trace_links.md` when `--execute-orchestrator` is used
- `agents/runs/{run_id}/run_metrics.md` when `--execute-orchestrator` is used
- `agents/runs/{run_id}/orchestration_report.md`

Generated JSON files remain ignored local runtime artifacts.

## Status Semantics

- `dry_run`: no files were written.
- `complete`: written run completed without deterministic quality findings, provider errors, analysis errors/skips, memory finalization issues, or SDK quality/freshness findings.
- `needs_review`: provider errors, analysis errors/skips, quality findings, finalization issues, SDK errors, SDK quality findings, or actionable SDK output from dry-run provider/analysis inputs exist.

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
- Repeated fresh runs are idempotent at the generated-artifact level because live execution cleans prior generated run artifacts before rebuilding them.
- Successful SDK file update proposals are routed through `orchestrator_update_proposals.md` and duplicate-safe human-review queue rows before any company-file writer can apply them.
