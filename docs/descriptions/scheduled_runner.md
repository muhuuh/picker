# Scheduled Runner

Last updated: 2026-05-06

## Purpose

The scheduled runner is the deterministic weekly workflow wrapper. It chains the already-built repo loaders, manifest generation, provider task runner, analysis task runner, run summary, quality report, memory finalization, and bounded memory-writer review.

Implementation: `stock_research/scheduled_runner.py`.

This is not the LLM orchestrator yet. It intentionally stops at the framework decision boundary.

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

Optionally call the live OpenAI-backed memory writer:

```powershell
python -m stock_research run-weekly --write --execute-memory-writer
```

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
  -> orchestration_report
  -> agent framework decision boundary
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
- `agents/runs/{run_id}/orchestration_report.md`

Generated JSON files remain ignored local runtime artifacts.

## Status Semantics

- `dry_run`: no files were written.
- `complete`: written run completed without deterministic quality findings, provider errors, analysis errors/skips, or memory finalization issues.
- `needs_review`: provider errors, analysis errors/skips, quality findings, or finalization issues exist.

## Current Boundary

After this runner, the agent framework decision is now resolved:

- Selected framework: OpenAI Agents SDK.
- Dedicated plan: `docs/plans/openai_agents_sdk_orchestration_backlog.md`.
- Dedicated scratchpad: `docs/scratchpads/openai_agents_sdk_orchestration_scratchpad.md`.

The next pending step is to implement a focused SDK runtime slice. Until that exists, `run-weekly` still stops after deterministic finalization and orchestration report generation.
