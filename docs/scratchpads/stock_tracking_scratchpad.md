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
- 2026-05-17: Fresh user-follow-up research ran for TE, IREN, AXTI, AMBA, AVAV, KRKNF, and OSS using Grok/X plus Exa. Interim findings are preserved in `agents/runs/2026-05-17_followup_user_questions/follow_up_research_working_notes.md` before final report/company-file updates.
- 2026-05-17: Follow-up research found one important correction: AXTI should not be framed as simply avoiding 6-inch InP; current evidence says AXTI is actively scaling/ramping 6-inch. The older "competitors may fail at 6-inch and shift back to AXTI 4-inch" angle is unverified and needs company-file correction.
- 2026-05-17: Smaller/OTC holdings still need stronger valuation sanity checks. AXTI surfaced suspicious financial snapshot values in prior reports, so valuation conclusions should require cross-provider confirmation.
- 2026-05-17: Final follow-up report was written to `agents/runs/2026-05-17_followup_user_questions/follow_up_research_report.md`. TE, IREN, AXTI, AMBA, AVAV, KRKNF, and OSS company files now have dated follow-up notes plus updated top-level thesis/opinion context.
- 2026-05-17: Cross-provider valuation sanity checks are now implemented in code. Extreme 52-week ranges, price/range mismatches, market-price-only coverage, and single-provider P/E can downgrade valuation metric confidence and surface explicit warnings in financial reviews, opportunity assessments, and company-file factual updates.
- 2026-05-17: Follow-up run artifacts are drill-down evidence, not active memory. Durable company conclusions should live in company files; operational lessons live in `agents/memory/`; old run artifacts can be indexed/archived after their conclusions are promoted.
- 2026-05-17: HRQ candidate rows still need better human ergonomics. The user should not approve/reject random ticker symbols; candidate digest rows need mini-thesis context or should be left open/marked `needs_more_research`.
- 2026-05-17: Redid the lost native web research and persisted it immediately in `agents/runs/2026-05-17_followup_user_questions/follow_up_web_research_redo.md`; linked it from TE, IREN, AXTI, AMBA, AVAV, KRKNF, and OSS company files.
- 2026-05-17: Human review digest now loads linked candidate-review context and stale/non-actionable open HRQ rows were marked `superseded`, reducing the live digest from 20 rows to 6 contextual rows.
- 2026-05-17: Google Sheet `new_stock_overview` is accessible via the Google Drive plugin. It has one tab, `Sheet1`, with headers: Date, Name, Ticker, Industry, Mcap, Forward PE, Forecast, Score, available, action, Comment.
- 2026-05-17: Proposed sheet journey fits the repo if treated as a lightweight pre-intake/inbox for user-discovered stocks. The durable workflow should still sync selected rows into repo artifacts before validation, verification, or monitoring promotion.
- 2026-05-17: Implemented the quick Sheet intake bridge. Sheet `action=research` rows can be passed to `python -m stock_research sheet-intake selected-rows --rows-json rows.json --write --queue-review`; this writes intake/candidate-review artifacts and optional HRQ rows, but does not add monitoring/holdings/rejected state.
- 2026-05-17: Live Sheet headers now include Source / link, Processing status, Repo link, and Last checked. Final dropdown model: Score=A+/A/A-/B+/B/B-/C+/C/C-/D+/D/D-, available=yes/no, action=research/add to monitoring/buy candidate/bought/ignore/rejected, and processing status=not processed/in research/done/needs fix. Blank action means no repo processing.
- 2026-05-17: Candidate follow-up now parses both older detailed candidate-review tables and current compact Evidence state tables, so Sheet-created candidate reviews can produce verification manifests.
- 2026-05-17: Live Sheet round-trip verified with ASTS and SIVE sample rows from the user's pasted report. Writing rows, reading values/validation metadata, updating processing status/Last checked, and reading updates back all worked through the Google Sheets connector.
- 2026-05-17: CLI dry-run verified action semantics: a `research` row is selected for intake, while a blank-action row is skipped.
- 2026-05-17: Final live Sheet read-back verified pragmatic dropdowns: action=research/add to monitoring/buy candidate/bought/ignore/rejected; Processing status=not processed/in research/done/needs fix; Score preserves B+.

## Open Questions

- Whether AAPL should remain as a real monitoring stock after workflow validation or be replaced by the user's actual watchlist.
- Whether repeated Sheet processing becomes annoying enough to justify a helper; current decision is to use Codex connector reads/writes first.

## Next Steps

- Decide whether to keep AAPL as a real monitored stock or replace it with the user's actual watchlist.
- Add Exa contents follow-up for high-value company-news URLs before deeper AAPL thesis/company-file updates.
- Regenerate a weekly/company report for AXTI or another small-cap example to confirm the new valuation sanity warnings appear in the final human-facing output when provider coverage is suspicious.
- Continue improving candidate-review evidence quality for newly generated rows; the digest now has contextual rows, but source candidate-review files should keep improving the reason-to-care and risk/check fields.
- Run the first real Sheet-to-repo processing pass with actual `action=research` rows, then decide whether a helper is needed.

## Risks / Gotchas

- AAPL is currently a workflow validation seed, not an investment recommendation.
- Keep detailed financial reasoning in the company file and evidence artifacts, not only in the CSV row.
- Current run evidence count includes older provider smoke packets in the same run folder; future clean runs should use a fresh run id for cleaner metrics.
- Grok/X follow-up findings are valuable for sentiment and hidden angles but remain social signals until verified with Exa, company IR, filings, or financial-provider evidence.
- Do not make the Google Sheet the source of truth for monitored holdings. It should stay quick capture; repo CSVs, company files, run artifacts, and human-review queue remain durable state.
- Sheet-added financial metrics are useful for triage but should be refreshed and source-backed before they affect research conclusions.
- `action=buy candidate` is only a triage label. It is not a buy instruction and should not bypass verification or human approval.
- `action=add to monitoring` is an outcome after research/approval, not the trigger for Codex to run research. The trigger is `research`.

## Commands / Environment Notes

- Current repo path: `C:\Users\valen\Documents\Code\stocks`.
- AAPL workflow validation command: `python -m stock_research analysis-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json --execute --today 2026-05-04`.
- Full validation commands: `python -m stock_research provider-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json --execute --today 2026-05-04`, then `run-summary`, `quality-report`, and `memory finalize-run`.
- Company news validation command: `python -m stock_research analysis-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json --execute --task-id company_news_review_aapl --today 2026-05-04`.
- Sheet intake command: `python -m stock_research sheet-intake selected-rows --rows-json rows.json --write --queue-review`.
