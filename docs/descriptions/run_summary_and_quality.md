# Run Summary And Quality Reports

Last updated: 2026-05-18

## Purpose

Weekly/manual runs should produce human-readable outputs before memory finalization.

Current deterministic commands:

```powershell
python -m stock_research run-summary --run-id RUN_ID --write
python -m stock_research quality-report --run-id RUN_ID --write
python -m stock_research human-report synthesis-pack --run-id RUN_ID --write
python -m stock_research quality-report --run-id RUN_ID --write --require-final-reports
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
- recommended updates needing human review,
- human-facing markdown quality issues in the final digest, Codex review, run summary, human-review digest, human-review digest summary, opportunity audit reports, company-research reports, and `reports/human_synthesis/*_final_human_report.md` reports.
- when `--require-final-reports` is passed, missing canonical `reports/human_synthesis/{TICKER}_final_human_report.md` targets for every synthesis pack.
- orphan `reports/human_synthesis/*_final_human_report.md` reports that do not have a matching synthesis pack.

Generated `.json` outputs are local runtime artifacts and are ignored by Git. The `.md` summary/report/finalization files are the reviewable artifacts intended for normal repo inspection. After finalization and promotion guardrails pass, ignored JSON can be removed with `python -m stock_research artifact-hygiene cleanup-json --write`; dry-run the command first.

## Human Synthesis Packs

Implementation: `stock_research/human_synthesis_pack.py`.

Outputs:

```text
agents/runs/{run_id}/reports/human_synthesis/{TICKER}_synthesis_pack.json
agents/runs/{run_id}/reports/human_synthesis/{TICKER}_synthesis_pack.md
```

These packs are the handoff for Codex app final-report writing. They collect the deterministic opportunity assessment, financial/news reviews, Grok/X social signal, auxiliary Grok web context, and company-file links, then instruct Codex to write the human report from first principles. The opportunity assessment remains useful for audit and source coverage; it should not be treated as the final reader experience.

The quality gate checks the generated `*_final_human_report.md` reader artifacts, not the `*_synthesis_pack.md` inputs.

In the scheduled Codex-supervised runner, the normal quality report is written after the deterministic final digest, human-review digest, category-state update, and synthesis-pack generation so it can scan the actual human-facing artifacts that exist before Codex app writes the final narrative layer. After Codex writes `codex_supervised_review.md` and every `*_final_human_report.md`, Codex must rerun `quality-report --write --require-final-reports`; that post-Codex gate is the completion check for the final report layer.

## Workflow Role

```text
provider-tasks --execute
  -> analysis-tasks --execute
  -> run-summary --write
  -> quality-report --write
  -> human-report synthesis-pack --write
  -> memory finalize-run
  -> Codex writes codex_supervised_review.md and canonical *_final_human_report.md files
  -> quality-report --write --require-final-reports
```

## Current Validation

On 2026-05-04, AAPL was added as a monitoring workflow seed. The manifest planned AAPL provider tasks and AAPL analysis tasks. Provider tasks, `company_news_contents_follow_up_aapl`, `company_news_review_aapl`, `financial_compare_aapl`, `financial_review_aapl`, `run-summary`, `quality-report`, and `memory finalize-run` were executed successfully.

The run finalization is currently `complete`: quality findings are zero, reflection issues are zero, and all evidence packets validate.
