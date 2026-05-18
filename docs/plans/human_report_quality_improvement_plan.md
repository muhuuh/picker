# Human Report Quality Improvement Plan

Last updated: 2026-05-18

## Goal

Improve opportunity assessments and final digests so they are easier to read, less repetitive, more actionable, and better at turning raw provider findings into an investor-useful narrative.

## Scope

- Opportunity assessment markdown.
- Final weekly digest markdown.
- Report quality gates that catch repeated claims before human review.
- Grok/xAI collection strategy for business context, latest news, analyst context, and consensus gaps beyond X sentiment.

## Findings From AMBA / KRKNF Review

- The raw Grok X artifacts already contain strong investor-useful sections: X pulse, trend evolution, bull/bear claims, notable accounts, rumors, and research checks.
- The human opportunity reports repeat the same claims across Verdict, Executive Read, Core Thesis, What Changed, Tailwinds, Trend Evolution, X Split, Non-obvious Insights, Decision Table, and Recommended Next Action.
- The sample Grok PDFs are easier to read because they use a first-principles order: business, industry, X sentiment, financials, analyst forecasts, latest news, then assessment.
- Our workflow has more evidence depth than the sample PDFs, but the report assembler currently exposes too much of the sub-report stitching.
- Alpha/financial provider gaps can leave forward P/E and analyst target context missing. A Grok web deep-dive can help identify coverage gaps, but material facts still need verification through financial providers, filings, Exa, or company sources.

## Action Plan

- [x] Compare AMBA/KRKNF raw artifacts, generated opportunity reports, and the attached Grok PDF reports.
- [x] Identify repetition sources in `stock_research/opportunity_assessment.py`.
- [x] Add cross-section de-duplication to opportunity assessment markdown.
- [x] Reduce repeated summary/table language in opportunity assessment data builders.
- [x] Add a report-quality gate for repeated long claims.
- [x] Improve final digest formatting so it does not repeat the same ticker claims across summary/news/social/positives.
- [x] Add an xAI Grok `web_search` deep-dive provider path for business context, latest news, valuation/analyst coverage gaps, and research checks.
- [x] Document the new Grok web path and guardrails.
- [x] Regenerate AMBA/KRKNF opportunity reports from existing artifacts to verify the reading flow.
- [x] Run targeted unit tests.
- [x] Run a live AMBA Grok `web_search` smoke test and compare it against the deterministic AMBA report and attached Grok PDF.
- [x] Write a Codex first-principles AMBA synthesis benchmark and assess the content by reading the report, not only by checking de-dup metrics.
- [x] Add per-ticker human synthesis packs so Codex app GPT-5.5 high can write final reports from evidence instead of patching deterministic report sections together.
- [x] Test a real AMBA `reports/human_synthesis/{TICKER}_final_human_report.md` written from the synthesis pack plus Grok web/X evidence.
- [x] Confirm Codex app is the primary final-report writer; API/OpenRouter is only a remote/headless fallback, not a competing quality target.
- [x] Make the Codex review pack list explicit final human report targets for every synthesis pack.
- [x] Write 2026-05-16 per-ticker final human reports for all ten synthesis packs and verify the report-quality gate is clean.
- [x] Promote the accepted AMBA final-report shape into synthesis-pack instructions and final-report quality gates so manual runs cannot drift into ad hoc report formats.
- [x] Add final-report depth requirements so correct headings are not enough; final reports must preserve opportunity-assessment insight coverage while removing repetition.
- [x] Add a post-Codex quality gate that requires every synthesis pack to have its canonical final human report and flags orphan final reports.
- [x] Update the active biweekly Codex automation prompt so scheduled runs perform the canonical final-report write and post-Codex quality gate.
- [x] Update Codex exec-policy rules so the scheduled automation can run the post-Codex quality gate.

## Guardrails

- Treat Grok X output as social signal, not fact.
- Treat Grok web output as auxiliary coverage-gap evidence until verified.
- Do not add buy/sell/trade instructions.
- Avoid report sections that are just pasted provider sub-summaries.
- Every report should surface the main decision gates and next checks clearly.

## Next Backlog Step

On the next fresh scheduled run, verify that same-run Grok web artifacts are present in the synthesis packs, have Codex app write all `reports/human_synthesis/*_final_human_report.md` targets, and rerun `quality-report --write --require-final-reports` before treating the run as complete. Keep `reports/opportunity_assessment/` audit-only.

## 2026-05-17 Update

- Implemented cross-section report de-duplication and less repetitive summary/table language.
- Added a deterministic repeated-long-claim gate to human report quality checks and wired it into run quality reports.
- Added Grok `web_search` company deep-dive tooling, CLI support, provider-runner support, model routing, and weekly manifest tasks.
- Regenerated all 2026-05-16 opportunity reports and the final digest; the run quality report now has zero findings.
- Remaining risk: the new Grok web path is implemented and planned in new manifests, but it still needs a live smoke test and source-quality comparison before relying on it for scheduled conclusions.

## 2026-05-17 AMBA Synthesis Update

- Live AMBA Grok web smoke test succeeded and surfaced useful non-sentiment gaps: analyst target range, forward valuation context, cash/debt color, competitive frame, and immediate May 28 earnings proof points.
- Visual inspection of the attached AMBA Grok PDF confirmed that its one-pass report structure is more readable than our deterministic report: business/technology, industry/competition, X sentiment, financials, analyst forecasts, news, and overall assessment.
- The Codex synthesis benchmark was the best human read because it combined Grok-style storyline with repo evidence discipline and explicit uncertainty labels.
- Decision: de-duplication is only a gate. The final human report needs a first-principles synthesis layer. Deterministic opportunity assessment remains an audit/evidence artifact.

## 2026-05-17 AMBA Final Report Test

- Wrote `agents/runs/2026-05-16_weekly/reports/human_synthesis/AMBA_final_human_report.md` from the synthesis pack plus AMBA Grok web/X artifacts.
- The final report is materially better than the deterministic audit report because it has a clear storyline: business context, what changed, social signal, financial evidence, bull/bear cases, thesis changers, and next checks.
- Wired `*_final_human_report.md` artifacts into `quality_report`; `*_synthesis_pack.md` remains an input artifact, not a reader-facing output.
- Clarified the user decision: final writing stays inside Codex app supervision. API/OpenRouter is only fallback/debug infrastructure for runs where Codex app cannot be used.

## 2026-05-17 Full Final-Report Layer Update

- Wrote all ten 2026-05-16 per-ticker final human reports under `reports/human_synthesis/*_final_human_report.md`.
- Updated the Codex review pack so every synthesis pack has an explicit final-report target; the 2026-05-16 pack now shows 10/10 targets present.
- Moved scheduled quality-report generation after final digest, human-review digest, category-state update, and synthesis-pack generation so the gate scans the actual deterministic human-facing artifacts before Codex writes the final narrative layer.
- The quality report for `2026-05-16_weekly` has zero findings after scanning final digest, human-review digest, opportunity audits, and final human reports.

## 2026-05-18 Final-Report Contract Correction

- User feedback exposed a real workflow defect: a manual LPKF/Sivers run used the correct `*_final_human_report.md` destination but drifted into an ad hoc report shape instead of the established AMBA-style final report.
- Fixed the process by adding the AMBA final-report contract to synthesis-pack instructions and by adding a report-quality gate for missing final-report provenance or required sections.
- Regenerated the LPKF and Sivers final human reports in the established structure rather than creating another side report.

## 2026-05-18 Depth Correction

- User feedback exposed a second workflow defect: enforcing the final-report shape still allowed reports that were too high-level and did not preserve the opportunity assessment's useful insight depth.
- Clarified the true standard: final reports must be cleaner than opportunity assessments, not thinner. They must include source-backed developments, market context, X trend and notable accounts, bull/bear social claims, rumors, under-discussed angles, valuation gaps, decision table/scorecard, thesis changers, and next checks.
- Added a final-human-report depth gate and regenerated LPKF/Sivers final reports again in the same `*_final_human_report.md` targets.

## 2026-05-18 Canonical Path And Post-Codex Gate

- User feedback exposed a third workflow defect: the automation handoff named final-report targets, but the deterministic quality command did not yet have a post-Codex mode that requires those targets to exist.
- Added `quality-report --require-final-reports` so the post-Codex completion check flags missing canonical final reports and orphan final reports without breaking the pre-Codex deterministic run phase.
- Updated the Codex review pack so Codex must write the canonical final report targets, avoid side reports, and rerun the post-Codex quality gate after final report writing.
- Updated the active biweekly Codex automation prompt to require the same behavior during scheduled runs, not only manual runs.
- Updated and verified the active Codex exec-policy rules so both the main scheduled command and the post-Codex quality command are allowed.
