# Analysis Task Runner

Last updated: 2026-05-04

## Purpose

The analysis task runner executes deterministic post-provider analysis tasks from a run manifest.

Implementation: `stock_research/analysis_runner.py`.

Current command:

```powershell
python -m stock_research analysis-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json
python -m stock_research analysis-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json --execute
```

Like `provider-tasks`, it is dry-run by default. Use `--execute` to write artifacts.

## Current Supported Tools

- `financial_compare`
- `financial_review`
- `company_news_contents_follow_up`
- `company_news_review`

## Workflow Role

```text
manifest
  -> provider-tasks --execute
  -> analysis-tasks --execute
  -> future run summary and quality report
  -> memory finalize-run
```

For financial analysis:

```text
financial provider evidence packets
  -> financial_compare analysis task
  -> financial_review analysis task
```

`financial_review` tasks depend on the matching `financial_compare` task. If a selected comparison task fails, the selected dependent review task is skipped.

For company news:

```text
Exa company-news provider packet
  -> company_news_contents_follow_up analysis task
  -> company_news_review analysis task
```

`company_news_contents_follow_up` runs Exa `/contents` for selected high-value URLs from the news packet. `company_news_review` depends on it in the manifest and should treat search-highlight-only evidence as `partial_review`.

## Filters

```powershell
python -m stock_research analysis-tasks --manifest PATH --tool financial_compare
python -m stock_research analysis-tasks --manifest PATH --task-id financial_review_aapl
python -m stock_research analysis-tasks --manifest PATH --limit 2
```

## Guardrails

- Execute provider tasks first so analysis tasks have evidence packets to consume.
- Keep the runner deterministic; LLM synthesis belongs in later specialist/orchestrator layers.
- Treat skipped tasks as run-quality issues unless intentionally filtered.
- Run finalization after analysis and future run-summary/quality-report generation.
