# Portfolio Research Quality Scratchpad

> Living short-term memory for the recurring portfolio update and on-demand research overhaul.
> Keep entries short, evidence-linked, and free of secrets.

Last updated: 2026-08-16

## Goal

- Make the recurring research product a trustworthy, insightful replacement for the user's own X/web research.
- Produce one useful executive update about current holdings, monitored stocks, and the industries that affect them.
- Keep on-demand company and industry deep research separate from the recurring update while reusing provider and evidence functions.
- Learn from reader feedback and run outcomes without creating an opaque or overcomplicated memory system.

## Current Task Plan

- [x] Read repo memory, operational memory, existing scratchpads, plans, and workflow descriptions.
- [x] Map portfolio state, automation, provider routing, synthesis, quality gates, and learning flow.
- [x] Inspect the latest completed recurring run and compare its stated quality status with the actual reader output.
- [x] Create a broader prioritized plan for the product-quality overhaul.
- [x] Receive approval to implement the first P0 slice from the linked plan.
- [x] Implement P0.1 characterization fixtures and reader-value rubric.
- [x] Implement the P0.2 research-profile/state-boundary foundation.
- [x] Implement and live-verify P0.3 Grok 4.6 routing and provenance.
- [x] Complete P0.1a test-credibility hardening and restore a clean full-suite run.
- [x] Complete P0.4 full-evidence preservation, safe excerpts, and selected full-claim retrieval.

## Current Product Map

- Durable portfolio membership is repo-owned:
  - `stock_tracking/current_holdings/current_holdings.csv`: 11 current holdings.
  - `stock_tracking/monitoring/monitoring.csv`: 1 monitored stock (`PENG`).
  - `stock_tracking/rejected/rejected.csv`: 1 rejected stock (`KRKNF`).
- The Google Sheet `new_stock_overview` is an idea inbox, not portfolio state. It only enters repo research after an explicit user request.
- The recurring entrypoint is `stock_research.scheduled_runner.run_weekly_research_workflow`; the CLI name is still `run-weekly` even though the Codex automation cadence is biweekly.
- The Codex automation `biweekly-holdings-and-monitoring-research` is currently `PAUSED`.
- Default recurring execution gathers deterministic provider/analysis artifacts, then asks one Codex run to write a run-level review plus one final report for every tracked ticker.
- A separate manual industry/theme path exists in `stock_research.market_research_runner`, but it is discovery-oriented and does not yet implement the desired full industry deep-research product.

## Validated Findings

### Product Shape

- The recurring manifest is company-centric. It scans every holding/monitoring ticker but does not automatically derive and synthesize the industries represented by the portfolio.
- The only active recurring research priority is broad `US and Europe stock discovery`; this is not a portfolio-industry coverage model.
- The recurring output creates a long final report for all 12 tracked names every run, even when little changed. That encourages re-explaining background instead of surfacing material deltas.
- The current docs disagree about which artifact is the primary reader surface: `final_digest.md`, opportunity assessments, per-ticker final reports, and `codex_supervised_review.md` are each described as primary in different places.
- Generic `route-request` stock research mutates monitoring state by default. A request to research a company is therefore not cleanly separated from a request to start monitoring it.

### Provider And Evidence Quality

- Previous xAI routing used `grok-4.3` in config, provider defaults, manifest fallbacks, tests, and docs.
- xAI documentation updated on 2026-08-12 now explicitly documents `grok-4.6`, X Search, Web Search, and `reasoning_effort`. The authenticated `/v1/models` check on 2026-08-16 confirmed that the configured account exposes `grok-4.6` directly.
- The repo now requests `grok-4.6`, checks availability with the authenticating key before live research, records requested/resolved model, tool, reasoning effort, resolution source, and fallback reason, and refuses to silently replace an unavailable X-search lane with generic web search.
- Grok is correctly used for X-native research, but the default workflow also runs a full Grok web deep dive for every ticker. That overlaps with Exa/company/financial lanes and increases synthesis volume.
- Exa company-news searches have no explicit publication-date window in the recurring manifest.
- Exa contents follow-up selects the first three returned URLs, not a source-diverse, materiality-ranked set. Syndicated or low-authority results can crowd out filings, IR, or strong reporting.
- Prior behavior shortened Exa evidence to 800/1,000 characters and Grok packet evidence to 4,000 characters. Canonical selected text is now preserved; bounded packet summaries use separate complete-sentence excerpts and raw path/selectors.
- Prior behavior replaced visible ellipses with periods. The formatter now refuses incomplete source text or stops at the last real sentence boundary; selected full evidence remains available through the SDK claim tool.

### Reader Report Quality

- Latest inspected run: `agents/runs/2026-07-04_weekly/`.
- Its post-Codex quality gate reported zero findings, but the 12 final reports repeat the same 11 long boilerplate passages across every ticker.
- All 12 reports use the same five generic next checks, so company-specific research actions are diluted.
- Reports contain incomplete source fragments even though the truncation gate passes; examples end in fragments such as `machine.`, `sh.`, `and.`, or `if.`.
- The fixed 1,700-word depth floor rewarded padding. It has been removed; the gate now evaluates reader value and corpus repetition, although delta-specific coverage rules still belong in later profile work.
- The quality gate checks each file independently. It does not detect cross-company boilerplate, cross-run repetition, stale background reuse, claim novelty, source-tier quality, or whether a reader learned anything decision-relevant.
- The run-level Codex review is more useful than most per-company reports, but it still lacks an explicit portfolio-industry section and a clear change-since-last-update baseline.

### Learning Loop

- Scheduled reflection/finalization runs before Codex writes the final reader reports.
- The post-Codex step reruns `quality-report`, but it does not rerun reflection/finalization. Final-output defects and repairs therefore do not enter memory proposals.
- The latest run recorded 167 valid packets, zero issues, and zero memory proposals despite the final report defects above.
- Current reflection measures execution and packet validity, not reader usefulness, source yield, novelty, repeated boilerplate, or user feedback.
- There is no lightweight durable record for comments such as `useful`, `not useful`, `too repetitive`, `missed this expert`, or `wrong emphasis` tied to a report/run/provider lane.
- Operational memory injection is strongest in optional Agents SDK paths. The default Codex-supervised path mainly relies on broad instructions to read memory rather than a small, task-specific feedback context per writer.

## Working Direction

- Keep one shared provider/evidence foundation, but add explicit research profiles with separate manifests and report contracts:
  - recurring portfolio-and-industry update;
  - on-demand company deep research;
  - on-demand industry/theme deep research;
  - existing candidate discovery/verification as a related but separate flow.
- Recurring reports should be delta-first. Reuse stable company background from durable files and write long per-company reports only for material changes or explicit drill-down.
- Use Grok/X for community pulse, expert accounts/posts, narrative change, rumors, and early signals.
- Use Exa for current web/news discovery, primary-source finding, industry context, and selected full-content retrieval.
- Use filings, company IR, and normalized financial providers for verified financial/accounting facts. Exa can find those sources but should not replace them as the numeric source of truth.
- Synthesize each company independently from a bounded packet, then aggregate company deltas and portfolio industries into the executive report. Do not ask one context to author 12 long reports and the portfolio summary at once.
- Move quality and learning after the final reader artifacts. Structural validation, editorial evaluation, feedback capture, and memory proposals should evaluate the output the user actually reads.
- Keep learning simple: explicit reader feedback plus measured provider/report outcomes; promote only repeated or user-confirmed lessons to operational memory.

## Open Questions For User Validation

- Should the recurring update normally include only the executive report plus short per-holding delta cards, with full company reports generated only for material changes?
- Is portfolio membership enough, or should the repo store approximate portfolio weights so the executive report can rank impact by exposure? No broker credentials or private account data should be stored.
- Which X accounts or expert groups should be seeded as high-value sources? The workflow can still discover accounts outside the seed list.
- What is the desired normal reading time for the recurring executive report: about 5, 10, or 15 minutes?
- Should new-stock discovery remain part of the same biweekly automation or move to a lower-frequency separate research product?

## Next Steps

- Implement P0.5 portfolio/industry source-of-truth rules next.
- Complete the manifest/report builders behind the new profile contracts when implementing the recurring and on-demand product flows.
- Keep portfolio weights, normal report reading time, material-change deep-report behavior, and discovery cadence as explicit user/product decisions.
- Keep the automation paused until the new recurring report passes the golden comparison and a fresh dry run.

## Risks / Gotchas

- Keep the authenticated model check even though Grok 4.6 is now documented and available; account exposure and model aliases can still drift.
- Do not treat Grok/X output as verified fact, even when the account looks credible.
- Do not treat Exa highlights as full evidence or pick the first results without source/materiality ranking.
- Do not use report length as a proxy for insight depth.
- Do not mutate monitoring/holdings merely because the user asked for research.
- Do not rerun destructive generated-artifact cleanup for synthesis-only fixes unless provider artifacts will be rebuilt.
- The worktree already contains unrelated modified/generated files; implementation must preserve them and stage only explicitly requested files if publication is later requested.

## Evidence And Useful Commands

- Portfolio summary: `C:\Python313\python.exe -m stock_research summary`
- Current routing: `agents/model_routing.yaml`, `stock_research/model_routing.py`, `stock_research/providers/xai_grok.py`
- Recurring manifest: `stock_research/manifest.py`
- Scheduled flow: `stock_research/scheduled_runner.py`
- Reader handoff: `stock_research/human_synthesis_pack.py`, `stock_research/codex_review_pack.py`
- Quality gates: `stock_research/report_quality.py`, `stock_research/quality_report.py`
- Learning: `stock_research/memory_reflection.py`, `stock_research/run_finalization.py`
- Latest inspected run: `agents/runs/2026-07-04_weekly/`
- Historical report-quality plan: `docs/plans/human_report_quality_improvement_plan.md`
- New canonical overhaul plan: `docs/plans/portfolio_research_quality_overhaul_plan.md`

## 2026-08-16 P0.1-P0.3 Implementation Update

- Added `stock_research/report_characterization.py`, a six-dimension reader rubric, known-bad/positive fixtures, 12-report repetition coverage, and quality-report corpus integration.
- Re-evaluating `2026-07-04_weekly` now produces 36 findings: 25 cross-report boilerplate findings and 11 dangling-fragment report findings instead of the historical false-clean result.
- Added `stock_research/research_profiles.py` with explicit contracts and write permissions for `portfolio_update`, `company_deep_research`, `industry_deep_research`, and `candidate_discovery`.
- `route-request` now plans company/industry deep research without changing monitoring membership or creating a recurring industry priority.
- Added authenticated xAI model discovery, Grok 4.6 defaults, explicit reasoning effort, failure/fallback rules, and raw-artifact model provenance.
- Authenticated model check: requested/resolved `grok-4.6`, no fallback.
- Live Grok 4.6 smokes: GOOGL stock X Search returned 45 X citation sources; AI semiconductor supply-chain industry X Search returned 4 X citation sources; both packets validated with no unknowns.
- Verification completed: 37 targeted tests passed; `compileall`, repo validation, operational-memory validation, model/manifest assertions, and both authenticated Grok 4.6 live smokes passed.
- At the P0.1-P0.3 checkpoint, 187 tests ran with 5 import errors because the declared `openai-agents` package was not visible in that environment. P0.1a later resolved this; see the completion update below.
- Validation warning outside this slice: one rejected-company cooldown has expired, so that candidate may be reviewed again.

## 2026-08-16 Test Credibility Audit

- Verdict: the tests are not useless, but the current suite is not yet trustworthy enough to certify report usefulness or the whole workflow.
- The real `2026-07-04_weekly` recheck works and returns 36 findings: 25 exact cross-report repetitions and 11 fragment findings.
- The committed known-bad fixtures are short synthetic reports; the 12-report case repeats one synthetic paragraph under 12 real ticker names instead of freezing actual report excerpts.
- The two positive fixtures are synthetic and use placeholder URLs, so they do not prove that strong historical Grok/Exa evidence survives.
- `READER_VALUE_RUBRIC` is only a tuple whose dimension names are tested; no production evaluator scores material change, specificity, source quality, X insight, reader efficiency, or completeness.
- Exact duplicate detection works, but a probe with three paraphrases of the same generic idea produced zero findings.
- Fragment detection caught `and.` but missed `sh.` and `machine.` probes; it remains a narrow regex heuristic.
- The old active final-report quality gate still requires 1,700 words and keyword markers. Its golden test repeats `Depth sentence for realistic report coverage.` 260 times to pass, directly rewarding padding.
- Research-only routing tests prove the current empty-scaffold path does not add monitoring rows. They do not snapshot existing holdings/rejected/strategy/company state, and the profile permission helper is used only by its unit test rather than downstream writers.
- Grok 4.6 behavior is the strongest part: payload/provenance unit tests pass, two stored live responses contain all requested stock/industry sections, both evidence packets validate, and all 49 extracted sources are X URLs.
- Grok gaps: live checks are manual, fallback capability is hardcoded rather than proven by the model catalog, and negative-path/CLI/recorded-response tests are incomplete.
- Audit-time finding: test infrastructure was not healthy because the full 187-test command had 5 collection/runtime import errors and no repository CI configuration. This is resolved in the completion update below.
- Decision: complete P0.1a test credibility hardening before starting P0.4.

## 2026-08-16 P0.1a-P0.4 Completion Update

- Replaced synthetic known-bad and placeholder positive fixtures with sanitized excerpts and the historical zero-finding artifact from real run evidence.
- The six reader-value dimensions now execute in fixtures and production quality reports; exact and bounded near-duplicate corpus checks both run.
- Removed the 1,700-word/keyword gate and golden-test padding; concise source-specific output can pass, repeated padding fails efficiency.
- Added protected-state route snapshots, downstream permission rejection, Grok catalog/CLI/recorded-response negative paths, and Windows CI.
- Preserved complete selected Exa/Grok evidence, separated display excerpts and raw selectors, and exposed bounded packet summary plus on-demand full-claim SDK tools.
- Historical full-run recheck: 53 findings in under two seconds locally (25 exact boilerplate, 3 near-boilerplate, 14 per-file report defects, 11 reader-value completeness failures).
- Verification: focused 55-test set passed; report characterization 5/5 passed after bounding semantic comparisons; final full declared-dependency suite passed 289/289.
- Environment note: the restricted sandbox does not expose the normal Python user site, so SDK collection was verified outside that sandbox after installing the already-declared project dependencies. No new runtime dependency was added.
