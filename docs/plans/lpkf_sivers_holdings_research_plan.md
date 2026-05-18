# LPKF And Sivers Holdings Research Plan

Last updated: 2026-05-18

## Goal And Scope

- Add LPKF Laser & Electronics SE and Sivers Semiconductors AB to current holdings.
- Remove Kraken Robotics from current holdings after the user sold it.
- Run a focused automation-style research pass for only LPKF and Sivers.
- Preserve source-backed findings in run artifacts and company files.

## Action Plan

- [x] Read repo memory, operational memory, scratchpad, and relevant descriptions.
- [x] Inspect current holdings/rejected files and research workflow commands.
- [x] Create a two-ticker manual manifest for LPKF and Sivers.
- [x] Execute provider and analysis tasks for only those two tickers.
- [x] Write Codex-supervised final human reports from the generated synthesis packs.
- [x] Update holdings CSV/state and company files.
- [x] Move Kraken Robotics out of current holdings and preserve sale/removal context.
- [x] Run validation, quality checks, and targeted tests.
- [x] Update scratchpad and this plan with final status.

## Key Decisions

- Use `LPK.DE` for LPKF because the XETRA/Yahoo Finance identifier is needed by current provider tooling.
- Use `SIVE.ST` for Sivers because Nasdaq Stockholm/Yahoo Finance provider tooling uses that suffix.
- Treat Sivers Q1 2026 as pending because the company announced on 2026-05-13 that the Q1 report moved from 2026-05-20 to 2026-05-29.
- Treat Kraken Robotics as sold/removed from active holdings, not as a fresh research target.

## Updates

- 2026-05-18: Started focused holdings update and research run planning after reading required memory and workflow docs.
- 2026-05-18: Provider tasks, analysis tasks, run summary, quality report, and human synthesis packs completed for `LPK.DE` and `SIVE.ST`.
- 2026-05-18: Created final human reports and company files; updated current holdings/rejected CSVs; moved `KRKNF` to rejected/inactive tracking after the user-confirmed sale.
- 2026-05-18: Finalized run memory, final digest, Codex review pack, human-review digest, category-state updates, and operational memory for dotted ticker artifact lookup. Validation and full unittest suite passed.
- 2026-05-18: Corrected final-report process after user feedback. The LPKF/Sivers reports now use the established AMBA-style final human report contract, and the workflow instructions/quality gate enforce that structure for future runs.
- 2026-05-18: Regenerated SIVE.ST opportunity assessment/synthesis pack after removing repeated valuation-warning prose. Focused run quality report now has zero findings; full test suite passed.
- 2026-05-18: Corrected final reports again for depth after user clarified that final reports must keep opportunity-assessment insight density, not just the accepted structure. Same final report paths were updated; no side report was created.
- 2026-05-18: Updated the run-level Codex-supervised review to point readers to the full-depth `reports/human_synthesis/*_final_human_report.md` files first and to label opportunity assessments as audit artifacts.
- 2026-05-18: Added a deterministic post-Codex gate, `quality-report --require-final-reports`, so this run and future runs must prove every synthesis pack has its canonical final human report and no orphan final human reports.
- 2026-05-18: Updated the active biweekly Codex automation prompt to require canonical final report creation and the post-Codex gate in the next scheduled automation.
- 2026-05-18: Verified Codex exec-policy allowlist now permits both the main scheduled command and the post-Codex final-report quality command.
