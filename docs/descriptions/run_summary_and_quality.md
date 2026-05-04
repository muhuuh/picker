# Run Summary And Quality Reports

Last updated: 2026-05-04

## Purpose

Weekly/manual runs should produce human-readable outputs before memory finalization.

Current deterministic commands:

```powershell
python -m stock_research run-summary --run-id RUN_ID --write
python -m stock_research quality-report --run-id RUN_ID --write
```

## Run Summary

Implementation: `stock_research/run_summary.py`.

Outputs:

```text
agents/runs/{run_id}/run_summary.json
agents/runs/{run_id}/run_summary.md
```

The run summary currently captures:

- planned provider and analysis task counts,
- evidence packet counts,
- tracked tickers,
- provider packet counts,
- financial review statuses,
- company news review statuses,
- deterministic open items.

## Quality Report

Implementation: `stock_research/quality_report.py`.

Outputs:

```text
agents/runs/{run_id}/quality_report.json
agents/runs/{run_id}/quality_report.md
```

The quality report currently checks:

- evidence packet schema validity,
- planned provider tasks with no matching task-specific packet,
- missing run summary,
- recommended updates needing human review.

Generated `.json` outputs are local runtime artifacts and are ignored by Git. The `.md` summary/report/finalization files are the reviewable artifacts intended for normal repo inspection.

## Workflow Role

```text
provider-tasks --execute
  -> analysis-tasks --execute
  -> run-summary --write
  -> quality-report --write
  -> memory finalize-run
```

## Current Validation

On 2026-05-04, AAPL was added as a monitoring workflow seed. The manifest planned AAPL provider tasks and AAPL analysis tasks. Provider tasks, `company_news_contents_follow_up_aapl`, `company_news_review_aapl`, `financial_compare_aapl`, `financial_review_aapl`, `run-summary`, `quality-report`, and `memory finalize-run` were executed successfully.

The run finalization is currently `complete`: quality findings are zero, reflection issues are zero, and all evidence packets validate.
