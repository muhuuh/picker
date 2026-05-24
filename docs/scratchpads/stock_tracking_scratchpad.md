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

- 2026-05-18: Started a focused current-holdings update for LPKF Laser & Electronics SE and Sivers Semiconductors AB, with Kraken Robotics removed after the user sold it. Task plan: `docs/plans/lpkf_sivers_holdings_research_plan.md`.
- 2026-05-18: For provider compatibility, use `LPK.DE` for LPKF's XETRA listing and `SIVE.ST` for Sivers' Nasdaq Stockholm listing unless a broker-specific ticker requires a later override.
- 2026-05-18: Focused automation-style run `2026-05-18_manual-lpkf-sivers-holdings` completed provider and analysis tasks only for `LPK.DE` and `SIVE.ST`; final reports live under `reports/human_synthesis/`.
- 2026-05-18: LPKF conclusion is constructive-but-watch: Q1 order intake/book-to-bill improved and LIDE has advanced-packaging upside, but high-volume production orders are not yet confirmed.
- 2026-05-18: Sivers conclusion is neutral/high-risk: AI optics/SATCOM/LiDAR exposure is attractive, but 2025 restatements, Q1 delay to 2026-05-29, dilution, and valuation-data conflicts require human review before raising conviction.
- 2026-05-18: Fixed `human_synthesis_pack` dotted-ticker raw-artifact lookup so tickers like `LPK.DE` and `SIVE.ST` find slugged Grok/X and web artifacts (`lpk_de`, `sive_st`).
- 2026-05-18: Final checks passed: `python -m stock_research validate`, `python -m stock_research memory validate`, targeted `test_human_synthesis_pack`, and full `python -m unittest discover -s tests`.
- 2026-05-18: Added operational memory `orch-2026-05-18-dotted-ticker-artifact-slugs` through `python -m stock_research memory add` for dotted ticker artifact lookup.
- 2026-05-18: User correctly rejected the first LPKF/Sivers final reports as too high-level. Rewrote both final reports to include the missing automation-run insight layers: market context, Grok/X sentiment, rumors, underdiscussed angles, bull/bear tables, and concrete verification tasks.
- 2026-05-18: User correctly objected that the rewrite still drifted from the established workflow. Fixed the process: synthesis packs now require the accepted AMBA-style final report shape, the report-quality gate flags missing final-report provenance/sections, and LPKF/Sivers final reports were regenerated in the same `*_final_human_report.md` targets rather than as side reports.
- 2026-05-18: Regenerated the focused run quality report after the correction; it now has zero findings. Also fixed repeated valuation-warning text in opportunity assessments so deterministic audit artifacts do not fail the human-facing markdown quality gate.
- 2026-05-18: User clarified the actual final-report standard: not a short summary, but at least the same amount of investor-useful insight as opportunity assessments, rewritten with a clear story and less repetition. Regenerated LPKF/Sivers final reports again with full source-backed developments, market context, X trends/accounts, rumors, under-discussed angles, scorecards, valuation gaps, thesis changers, and next checks; added depth markers to the quality gate.
- 2026-05-18: Direct quality check shows `LPK.DE_final_human_report.md` has 3,359 words and `SIVE.ST_final_human_report.md` has 3,289 words, both with zero human-facing markdown findings under the stricter final-report depth gate. Focused run quality report is back to zero findings.
- 2026-05-18: User correctly challenged that final reports also need workflow fit, not just better prose. Added `quality-report --require-final-reports` as the post-Codex completion gate, updated the review pack to require canonical `reports/human_synthesis/*_final_human_report.md` targets and forbid side reports, and documented that the default pre-Codex quality report is not the final completion gate.
- 2026-05-18: Updated active biweekly Codex automation prompt so the next scheduled run must write every canonical per-ticker final report, avoid side/ad hoc reports, and rerun `quality-report --require-final-reports` before finishing.
- 2026-05-18: Updated Codex exec-policy rules to allow the direct post-Codex `quality-report --run-id ... --write --require-final-reports` command; verified both the post gate and main scheduled command return `allow`.
- 2026-05-19: Started focused monitoring research for Penguin Solutions Inc. (`PENG`). Added `PENG` to monitoring, created `stock_tracking/stock_info_files/monitoring/PENG.md`, and created plan `docs/plans/penguin_solutions_monitoring_research_plan.md`. Run id: `2026-05-19_manual-penguin-solutions-monitoring`.
- 2026-05-19: Completed PENG-only Codex-supervised workflow. Provider and analysis tasks ran only for `PENG`; canonical final report is `agents/runs/2026-05-19_manual-penguin-solutions-monitoring/reports/human_synthesis/PENG_final_human_report.md`; post-Codex `quality-report --require-final-reports` passed with zero findings.
- 2026-05-19: PENG monitoring thesis is neutral/high-risk: Integrated Memory growth, raised FY2026 guidance, and AI/HPC logo wins justify monitoring, but conviction needs Q3/Q4 proof of revenue conversion, margin quality, and cash flow.
- 2026-05-20: Manual TE social-post research combined local TE reports with fresh web sources. Key insight: the current rally is now a three-way narrative fight between an AI-infrastructure fund 13F signal, source-backed G1/G2 operating progress, and FEOC/tax-credit short-seller risk. Best post framing is not "solar stock up" but "AI power bottleneck is pulling domestic solar manufacturing into the AI infrastructure trade."
- 2026-05-20: LPKF AGM counter-motion checked. Shareholder Prof. Dr. Hans-Ingo Radatz is asking shareholders to deny management-board discharge because he wants an immediate capital increase and faster LIDE/Advanced Packaging scaling instead of North Star cost discipline. Management recommends rejecting it and says cost savings fund growth rather than replace it; the board does not rule out a capital increase for value-creating growth.
- 2026-05-22: Prepared concise X framing for the LPKF AGM counter-motion. Plain-language angle: "refuse discharge" is a governance protest/no-confidence vote, not an instruction that management must stop saving money; the investment issue is whether LPKF should keep funding LIDE through disciplined North Star savings or raise capital to accelerate Advanced Packaging before confirmed volume orders.
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
- 2026-05-17: Google Sheet `new_stock_overview` is accessible via the Google Drive plugin. It has one tab, `Sheet1`; current headers include Date, Name, Ticker, Industry, Mcap, Forward PE, P/S, Forecast, Score, available, action, Comment, Source / link, Processing status, Repo link, and Last checked.
- 2026-05-17: Proposed sheet journey fits the repo if treated as a lightweight pre-intake/inbox for user-discovered stocks. The durable workflow should still sync selected rows into repo artifacts before validation, verification, or monitoring promotion.
- 2026-05-17: Implemented the quick Sheet intake bridge. Sheet `action=research` rows can be passed to `python -m stock_research sheet-intake selected-rows --rows-json rows.json --write --queue-review`; this writes intake/candidate-review artifacts and optional HRQ rows, but does not add monitoring/holdings/rejected state.
- 2026-05-17: Live Sheet headers now include Source / link, Processing status, Repo link, and Last checked. Final dropdown model: Score=A+/A/A-/B+/B/B-/C+/C/C-/D+/D/D-, available=yes/no, action=research/add to monitoring/buy candidate/bought/ignore/rejected, and processing status=not processed/in research/done/needs fix. Blank action means no repo processing.
- 2026-05-17: Candidate follow-up now parses both older detailed candidate-review tables and current compact Evidence state tables, so Sheet-created candidate reviews can produce verification manifests.
- 2026-05-17: Live Sheet round-trip verified with ASTS and SIVE sample rows from the user's pasted report. Writing rows, reading values/validation metadata, updating processing status/Last checked, and reading updates back all worked through the Google Sheets connector.
- 2026-05-17: CLI dry-run verified action semantics: a `research` row is selected for intake, while a blank-action row is skipped.
- 2026-05-17: Final live Sheet read-back verified pragmatic dropdowns: action=research/add to monitoring/buy candidate/bought/ignore/rejected; Processing status=not processed/in research/done/needs fix; Score preserves B+.
- 2026-05-17: Added pasted photonics/CPO ideas to live Sheet rows 4-6: AAOI score B, LITE score A-, and POET score B. `available` and `action` were left blank; `Processing status` is `not processed`.
- 2026-05-24: Re-clarified user workflow: Sheet rows marked `action=research` are a pre-monitoring research trigger; Codex can run per-stock deep-dive/verification first, then the user decides final Sheet/repo outcomes (`add to monitoring`, `rejected`, `ignore`, `needs_more_research`).
- 2026-05-24: Inspected live Sheet rows 7-17. User added 11 sparse rows with ticker-only entries and `action=research`: `$vpg`, `$peng`, `$occ`, `$mrvl`, `$arm`, `$soi`, `$aixa`, `$flnc`, `$fcel`, `$AMBQ`, `$LSCC`. This is enough for later intake in theory, but the leading `$` should be stripped or parser-normalized before repo processing.
- 2026-05-24: Added live Sheet `P/S` column next to `Forward PE` and updated the Sheet intake parser/docs so price-to-sales is preserved in candidate notes.
- 2026-05-24: Updated Sheet intake ticker normalization so leading `$` cashtag prefixes are stripped before validation and duplicate checks.
- 2026-05-24: First real Sheet intake run `2026-05-24_sheet-intake-new-stocks` selected 10 new candidates for verification and skipped PENG because it already exists in monitoring.
- 2026-05-24: Sheet candidate verification completed. Summary: likely monitor review first = MRVL, FLNC, VPG, LSCC, AIXA after exchange-aware financial refresh; speculative = AMBQ, OCC; likely pass = FCEL; SOI needs ticker correction because financial providers matched Solaris while news evidence matched Soitec.
- 2026-05-24: Sheet rows 7-17 were updated with repo links and processing status. PENG and SOI are `needs fix`; the other researched rows are `done`.

## Open Questions

- Whether AAPL should remain as a real monitoring stock after workflow validation or be replaced by the user's actual watchlist.
- Whether repeated Sheet processing becomes annoying enough to justify a helper; current decision is to use Codex connector reads/writes first.

## Next Steps

- Decide whether to keep AAPL as a real monitored stock or replace it with the user's actual watchlist.
- Add Exa contents follow-up for high-value company-news URLs before deeper AAPL thesis/company-file updates.
- Regenerate a weekly/company report for AXTI or another small-cap example to confirm the new valuation sanity warnings appear in the final human-facing output when provider coverage is suspicious.
- Recheck SIVE.ST after its Q1 2026 report scheduled for 2026-05-29 and reconcile market cap/share count/52-week-range data before using valuation conclusions.
- Recheck LPK.DE on any disclosed material LIDE production-equipment order or Q2 2026 order-intake update.
- Check the 2026-06-04 LPKF AGM outcome for management-board discharge, counter-motion support, and any new management comments on LIDE acceleration or capital increases.
- Recheck PENG after the next quarterly update for AI/HPC logo conversion, Integrated Memory durability, Advanced Computing stabilization, gross-margin quality, and cash-flow reconciliation.
- On the next scheduled/manual Codex-supervised run, confirm the quality report fails any final human report that does not follow the AMBA-style final-report contract.
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
- `sheet_intake.normalize_ticker` now strips leading `$`; ambiguous tickers still need exchange/source verification during research.

## Commands / Environment Notes

- Current repo path: `C:\Users\valen\Documents\Code\stocks`.
- AAPL workflow validation command: `python -m stock_research analysis-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json --execute --today 2026-05-04`.
- Full validation commands: `python -m stock_research provider-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json --execute --today 2026-05-04`, then `run-summary`, `quality-report`, and `memory finalize-run`.
- Company news validation command: `python -m stock_research analysis-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json --execute --task-id company_news_review_aapl --today 2026-05-04`.
- Sheet intake command: `python -m stock_research sheet-intake selected-rows --rows-json rows.json --write --queue-review`.
- LPKF/Sivers focused run commands used: `provider-tasks --manifest agents\runs\2026-05-18_manual-lpkf-sivers-holdings\manifest.json --execute --today 2026-05-18`, `analysis-tasks --manifest agents\runs\2026-05-18_manual-lpkf-sivers-holdings\manifest.json --execute --today 2026-05-18`, `run-summary`, `quality-report`, `human-report synthesis-pack`, `memory finalize-run`, `category-state update`, and `human-review digest`.
- PENG focused run commands used: `provider-tasks --manifest agents\runs\2026-05-19_manual-penguin-solutions-monitoring\manifest.json --execute --today 2026-05-19`, `analysis-tasks --manifest agents\runs\2026-05-19_manual-penguin-solutions-monitoring\manifest.json --execute --today 2026-05-19`, `run-summary`, `quality-report`, `human-report synthesis-pack`, `category-state update`, `company-file apply-factual-updates`, `memory finalize-run`, `memory writer-review`, and post-Codex `quality-report --require-final-reports`.
- Post-Codex final-report completion check: `python -m stock_research quality-report --run-id RUN_ID --write --require-final-reports`.
- Final report contract correction checks: `python -m stock_research validate`, `python -m stock_research memory validate`, `python -m unittest discover -s tests -p test_report_quality_golden.py`, `python -m unittest discover -s tests -p test_quality_report.py`, `python -m unittest discover -s tests -p test_human_synthesis_pack.py`, `python -m unittest discover -s tests -p test_opportunity_assessment.py`, and `python -m unittest discover -s tests`.
