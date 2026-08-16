# 2026-05-24 Sheet Full Deep-Dive Reports Plan

## Goal

Produce the actual canonical per-company final human reports for the Sheet stocks marked for research, so the user can review monitor/reject/ignore decisions from useful deep dives rather than candidate-routing summaries.

## Scope

- Run id: `2026-05-24_sheet-full-deep-dives`
- Companies/tickers: `VPG`, `PENG`, `OCC`, `MRVL`, `ARM`, `SOI.PA`, `AIXA.DE`, `FLNC`, `FCEL`, `AMBQ`, `LSCC`
- Corrected ticker assumptions:
  - Soitec is `SOI.PA`, not plain `SOI`.
  - AIXTRON is `AIXA.DE`, not plain `AIXA`.
- Do not promote any candidate to monitoring, holdings, or rejected without explicit user decision. `PENG` is already monitored and should stay a reference/refresh item.

## Checklist

- [x] Build a clean full-deep-dive manifest with full provider and analysis lanes.
- [x] Execute provider tasks: financial providers, Exa news/company search, Grok/X, and Grok web deep dive.
- [x] Execute analysis tasks: Exa contents follow-up, company-news review, financial compare/review, opportunity assessment.
- [x] Generate run summary, quality report, and human synthesis packs.
- [x] Write one canonical `reports/human_synthesis/{TICKER}_final_human_report.md` per company.
- [x] Rerun `quality-report --write --require-final-reports`.
- [x] Update the Google Sheet `Repo link` cells to point to the final reports, not candidate summaries.
- [x] Update scratchpad/docs with the corrected workflow distinction.

## Updates

- 2026-05-24: Plan created after user clarified that candidate-routing summaries are not acceptable; the required output is the established high-quality final human report workflow.
- 2026-05-24: Completed provider collection for all 11 companies with yfinance, FMP, Alpha Vantage, Exa, Grok/X, Grok web, plus Polygon/SEC where applicable.
- 2026-05-24: Completed 55 analysis tasks with no errors and generated run summary, opportunity assessments, and synthesis packs.
- 2026-05-24: Fixed `human_synthesis_pack` artifact matching so custom Sheet-run Grok artifacts named `sheet_full_xai_x_*` and `sheet_full_xai_web_*` are included in synthesis packs.
- 2026-05-24: Wrote all 11 canonical final human reports and reran `quality-report --write --require-final-reports`; final gate passed with zero findings.
- 2026-05-24: Updated live Google Sheet rows 7-17 so `Repo link` points to the canonical final reports, `Processing status=done`, `action=research`, and basic valuation fields are refreshed.
