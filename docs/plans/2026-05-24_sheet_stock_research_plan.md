# 2026-05-24 Sheet Stock Research Plan

## Goal

Research the stocks the user marked with `action=research` in the Google Sheet without promoting any of them to monitoring, holdings, or rejected state until the user reviews the results.

## Scope

- Source rows: live `new_stock_overview` Sheet rows 7-17.
- Current candidate tickers from the Sheet: VPG, PENG, OCC, MRVL, ARM, SOI, AIXA, FLNC, FCEL, AMBQ, LSCC.
- Active verification candidates: AIXA, AMBQ, ARM, FCEL, FLNC, LSCC, MRVL, OCC, SOI, VPG.
- Preserve the Sheet as the intake/status surface; preserve repo artifacts as the detailed source of truth.

## Checklist

- [x] Confirm the Sheet rows and action semantics.
- [x] Add the `P/S` column next to `Forward PE`.
- [x] Patch intake normalization so leading `$` cashtags process correctly.
- [x] Generate Sheet-intake and candidate-verification artifacts.
- [x] Run provider tasks for the verified candidates.
- [x] Run analysis tasks and candidate verification synthesis.
- [x] Update Sheet processing status/repo links.
- [x] Run validation checks and summarize recommendations for user review.
- [x] Remove visible `Source / link` column after user feedback and keep evidence in `Repo link`/repo artifacts.
- [x] Correct SOI to Soitec `SOI.PA`, rerun focused verification, and update the Sheet row.
- [x] Fix yfinance/financial_compare normalization so P/S and forward P/E from raw provider data can populate Sheet overview fields.

## Decisions

- `research` remains a pre-monitoring trigger. Final outcomes stay pending until the user explicitly chooses `add to monitoring`, `rejected`, `ignore`, `bought`, or another route.
- PENG may be blocked by duplicate monitoring state if it is already in the repo watchlist; do not create a duplicate monitoring record.

## Updates

- 2026-05-24: Plan created after confirming the user wants research on the new Sheet rows.
- 2026-05-24: Sheet intake created candidate-review and verification-plan artifacts for 10 candidates. PENG was skipped because it already exists in monitoring.
- 2026-05-24: Provider and analysis tasks completed. Candidate verification result and human-facing summary were written. Sheet status cells were updated: SOI and PENG need fixes; the other researched rows are done.
- 2026-05-24: Final checks passed: targeted Sheet-intake tests, repo validate, memory validate, rerun quality report with zero findings.
- 2026-05-24: Backfilled the live Sheet overview columns for rows 7-17 from the completed research artifacts after user feedback that status-only updates were not enough for review.
- 2026-05-24: User asked to remove the visible `Source / link` column and correct SOI to Soitec for completion research.
- 2026-05-24: Removed `Source / link` from the live Sheet and local intake schema/docs; corrected row 12 from conflicted `SOI` to `SOI.PA`; ran clean Soitec verification; wrote `agents/runs/2026-05-24_sheet-intake-soitec-soi/market_research/candidate_research_summary.md`; updated the Sheet row to `done`.
- 2026-05-24: Fixed the missing-column root cause for Soitec valuation fields by extending yfinance packet extraction and `financial_compare` mapping for forward P/E, P/S, revenue, and related valuation/profile metrics.
