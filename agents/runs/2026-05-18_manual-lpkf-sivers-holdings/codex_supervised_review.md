# Codex-Supervised Review: LPKF And Sivers Holdings

Generated: 2026-05-18
Depth-corrected: 2026-05-18 after final-report standard correction

## Scope

- Added LPKF Laser & Electronics SE as `LPK.DE`.
- Added Sivers Semiconductors AB as `SIVE.ST`.
- Removed Kraken Robotics (`KRKNF`) from current holdings after the user confirmed it was sold.
- Ran provider and analysis tasks only for `LPK.DE` and `SIVE.ST`.

## Outcome

The focused run produced useful evidence, but the first final human-facing reports were too compressed. The proper reader-facing reports are now the two full-depth files under `reports/human_synthesis/*_final_human_report.md`. They preserve the opportunity-assessment insight depth while removing repetition and giving the evidence a clearer story.

Post-Codex workflow check: `python -m stock_research quality-report --run-id 2026-05-18_manual-lpkf-sivers-holdings --write --today 2026-05-18 --require-final-reports` passed with zero findings after checking the canonical final report targets. There are no required side reports for these two companies.

Read these first for the actual company research:

- `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/reports/human_synthesis/LPK.DE_final_human_report.md`
- `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/reports/human_synthesis/SIVE.ST_final_human_report.md`

The opportunity assessments remain audit artifacts. They are useful for tracing score factors and evidence lanes, but they are not the final human report.

## LPKF Investor Read

LPKF is a constructive but unproven bottleneck thesis.

What matters:
- LIDE could be a critical process step if AI/HPC packaging moves toward glass substrates and through-glass vias.
- Q1 2026 revenue was weak, but order intake improved and book-to-bill reached 1.4.
- The company has source-backed language about Advanced Semiconductor Packaging progress and customer discussions for initial production equipment.
- X/community discussion is highly focused on LIDE/TGV adoption, possible Intel/customer links, 2027 mass production, and EUR 1B+ re-rating scenarios.
- The key bear case is simple: the stock rerated before a confirmed series-production order.

Full-depth final report: `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/reports/human_synthesis/LPK.DE_final_human_report.md`

## Sivers Investor Read

Sivers is a high-risk speculative platform thesis.

What matters:
- The company has exposure to AI optical interconnects/CPO, external lasers, mmWave/SATCOM, FWA, defense, and LiDAR.
- The market narrative is early and technical, not yet broad retail meme activity.
- Source-backed positives include 2025 restated revenue growth, a $453M opportunity pipeline in run artifacts, the strategic LiDAR ramp, and possible Nasdaq New York dual-listing preparation.
- Source-backed risks include restated financials, Q1 delay to 2026-05-29, negative EBIT/net result, directed issue dilution, and valuation-data conflicts.
- Social claims around Apple, Jabil/hyperscaler, GFS, and US-holder inflow are research leads only.

Full-depth final report: `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/reports/human_synthesis/SIVE.ST_final_human_report.md`

## Portfolio State Changes

- `stock_tracking/current_holdings/current_holdings.csv`: now includes `LPK.DE` and `SIVE.ST`, and no longer includes `KRKNF`.
- `stock_tracking/rejected/rejected.csv`: now includes `KRKNF` with reason `Sold by user and removed from current holdings.`
- `stock_tracking/stock_info_files/current_holdings/LPK.DE.md`: created.
- `stock_tracking/stock_info_files/current_holdings/SIVE.ST.md`: created.
- `stock_tracking/stock_info_files/rejected/KRKNF.md`: moved from current holdings and updated with sale/removal context.

## Open Risks

- SIVE.ST financial review is `needs_human_review` because provider market caps conflict and valuation sanity warnings were triggered.
- LPK.DE remains dependent on proof of LIDE production-equipment orders.
- Both reports use Grok/X as social signal, not verified fact.

## Next Steps

- Review SIVE.ST after the Q1 2026 report scheduled for 2026-05-29.
- Monitor LPK.DE for disclosed LIDE initial production-equipment orders and Q2 2026 order-intake evidence.
- Reconcile SIVE.ST market cap, share count, 52-week range, and P/E before using valuation conclusions.
