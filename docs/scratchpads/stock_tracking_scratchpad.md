# Stock Tracking Scratchpad

> Living memory for stock tracking files and workflow validation.
> Keep entries short and scannable. Do not store secrets.

## Goal

- Keep stock-tracking CSVs, company files, and category state files aligned with the automated research workflow.

## Current Plan

- [x] Add AAPL as a monitoring test stock.
- [x] Validate manifest provider and analysis task planning with AAPL present.
- [x] Execute deterministic analysis tasks using existing AAPL provider packets.
- [x] Generate run summary and quality report artifacts.
- [x] Execute full planned provider-task set for the AAPL weekly validation run.
- [x] Execute AAPL company-news specialist review.

## Key Decisions And Why

- 2026-05-04: Use AAPL in `monitoring`, not `current_holdings`, because it is a workflow validation stock and not an actual position.
- 2026-05-04: Generated run JSON should stay local/ignored; markdown run summaries and reports are the commit-friendly review artifacts.

## What We Learned

- `monitoring.csv` was empty before adding AAPL.
- `stock_tracking/stock_info_files/monitoring/` existed but had no company files.
- AAPL causes the weekly manifest to plan 10 provider tasks and 2 analysis tasks.
- `analysis-tasks --execute` successfully ran `financial_compare_aapl` then `financial_review_aapl`.
- Run summary and quality report artifacts now exist for `2026-05-09_weekly`.
- Full provider-task validation surfaced and fixed an Exa/Grok artifact naming issue: same-subject provider tasks now use task-specific packet/raw names.
- The current AAPL weekly validation run finalization is `complete` with zero deterministic quality findings and zero reflection issues.
- AAPL company-news review status is `ready_for_company_update`; it is a workflow validation artifact and should not be treated as an investment recommendation.

## Open Questions

- Whether AAPL should remain as a real monitoring stock after workflow validation or be replaced by the user's actual watchlist.

## Next Steps

- Decide whether to keep AAPL as a real monitored stock or replace it with the user's actual watchlist.
- Add Exa contents follow-up for high-value company-news URLs before deeper AAPL thesis/company-file updates.

## Risks / Gotchas

- AAPL is currently a workflow validation seed, not an investment recommendation.
- Keep detailed financial reasoning in the company file and evidence artifacts, not only in the CSV row.
- Current run evidence count includes older provider smoke packets in the same run folder; future clean runs should use a fresh run id for cleaner metrics.

## Commands / Environment Notes

- Current repo path: `C:\Users\valen\Documents\Code\stocks`.
- AAPL workflow validation command: `python -m stock_research analysis-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json --execute --today 2026-05-04`.
- Full validation commands: `python -m stock_research provider-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json --execute --today 2026-05-04`, then `run-summary`, `quality-report`, and `memory finalize-run`.
- Company news validation command: `python -m stock_research analysis-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json --execute --task-id company_news_review_aapl --today 2026-05-04`.
