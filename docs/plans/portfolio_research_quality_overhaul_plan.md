# Portfolio Research Quality Overhaul Plan

Last updated: 2026-08-16

Status: P0.1-P0.5 foundations are implemented and fully verified; the next slice is P1 change detection and higher-yield Exa/Grok selection

Scratchpad: `docs/scratchpads/portfolio_research_quality_scratchpad.md`

## Goal

Build a stock-research product that saves the user from manually browsing X, Google, company sites, filings, and financial pages while preserving the insight and judgment of that research process.

The finished system should provide:

1. A recurring biweekly executive update about current holdings, monitored stocks, and the industries that affect them.
2. On-demand deep research for a specific company without silently changing portfolio/watchlist state.
3. On-demand deep research for a specific industry or theme with company discovery and verification.
4. A small, auditable feedback loop that improves source selection, prompts, synthesis, and reader usefulness over time.

## Current Outcome Judgment

- Raw provider coverage: potentially strong; selected Exa/Grok evidence is now preserved without destructive clipping, while source selection/ranking and cross-source verification remain incomplete.
- Recurring report product: partial. It is structurally complete but too company-by-company, repetitive, and weak on portfolio industries and change detection.
- On-demand research: partial. Manual market discovery exists, but company/industry deep-research profiles and state-mutation boundaries are not explicit enough.
- Learning loop: partial. Operational packet/reflection machinery exists, but it evaluates before final reader output and does not capture reader feedback.
- Automation readiness: bad for unattended use until the report contract and final-output evaluation are corrected. The current automation is paused, which is appropriate during the overhaul.

## Target Product Contracts

### A. Recurring Portfolio And Industry Update

Purpose: tell the user what materially changed since the last accepted update and why it matters to the portfolio.

Default scope:

- all current holdings;
- monitored stocks at a lower default depth;
- industries/themes derived from portfolio exposure plus explicit recurring priorities;
- open high-impact human-review decisions;
- no automatic new-stock promotion or portfolio status move.

Primary reader artifact:

```text
agents/runs/{run_id}/reports/portfolio_update/portfolio_executive_update.md
```

Required content:

- bottom line and top 3-5 attention items;
- what changed since the last accepted run;
- portfolio-level industry/theme developments and read-throughs;
- per-holding delta cards: new facts, X/community shift, financial/valuation change, thesis impact, next check;
- monitored-stock exceptions;
- source/coverage warnings;
- open user decisions;
- links to evidence and any material-change company deep dives.

Normal behavior:

- stable background is referenced from durable company files, not rewritten every two weeks;
- unchanged stocks get a brief `no material change` card with coverage evidence;
- full per-company reports are written only when a materiality trigger fires or the user asks for one;
- target reading time is intentionally bounded after user validation.

### B. On-Demand Company Deep Research

Purpose: answer a specific company question from first principles with enough depth to make a monitoring/thesis decision.

Primary reader artifact:

```text
agents/runs/{run_id}/reports/company_deep_research/{TICKER}_deep_research.md
```

Required content:

- business and value chain;
- industry structure and competitive position;
- verified latest developments and filings;
- financial/valuation history and provider conflicts;
- Grok/X expert/community pulse, notable posts, narrative change, rumors, and source-quality notes;
- bull/bear cases, non-obvious angles, disconfirming evidence, thesis changers, and next checks;
- explicit answer to the user's question;
- no automatic monitoring/holding mutation.

### C. On-Demand Industry Or Theme Deep Research

Purpose: explain an industry, its current developments, value chain, expert debate, investable public companies, and verification gaps.

Primary reader artifact:

```text
agents/runs/{run_id}/reports/industry_deep_research/{SUBJECT}_deep_research.md
```

Required content:

- market structure, value chain, and major profit pools;
- latest source-backed developments and trend changes;
- X expert/community pulse, leading accounts/posts, hype, and contrarian views;
- incumbents, emerging companies, suppliers, bottlenecks, and second-order beneficiaries;
- verified versus unverified candidate table;
- industry risks, catalysts, scenarios, and next checks;
- candidate follow-up links without automatic promotion.

### D. Candidate Discovery And Verification

- Preserve the existing candidate-review/verification/promotion gates.
- Treat discovery as a separate product concern from the core portfolio update.
- Decide during P1 whether discovery remains biweekly, moves to a separate lower-frequency automation, or stays request-driven.

## Provider And Model Ownership

| Capability | Primary lane | Secondary/check lane | Must not become |
| --- | --- | --- | --- |
| X community sentiment, expert accounts/posts, narrative change, rumors, early signals | xAI Grok with `x_search` | Exa/primary-source verification | a verified-fact or financial source |
| Current web/news discovery, industry context, company/source discovery | Exa search | Grok/X for social edge | a headline-only synthesis lane |
| Full page evidence | Exa contents, company IR, filings | direct official page retrieval where available | first-three-results without ranking |
| U.S. filings/accounting | SEC EDGAR and company IR | Exa for discovery/contents | Grok/X-derived fact |
| Financial/valuation metrics | yfinance/FMP/Polygon/Alpha plus primary filings and deterministic reconciliation | Exa for analyst/source discovery | silently selected single-provider truth |
| Final recurring synthesis | bounded per-company delta synthesis plus portfolio/industry editor | Codex GPT-5.5 high in local mode | one giant prompt that writes 12 long reports at once |
| Deep-research synthesis | dedicated company or industry profile | optional API SDK fallback | reused recurring-update boilerplate |

Model compatibility note:

- Repo default is now `grok-4.6`.
- Official xAI docs updated on 2026-08-12 document Grok 4.6 with X Search, Web Search, and configurable reasoning effort.
- The authenticated `GET /v1/models` check confirmed on 2026-08-16 that the configured account exposes `grok-4.6`; live execution still records the resolved model and any fallback reason because account availability can drift.

Official references:

- https://docs.x.ai/developers/grok-4-6
- https://docs.x.ai/developers/tools/x-search
- https://docs.x.ai/developers/tools/web-search
- https://docs.x.ai/developers/rest-api-reference/inference/models
- https://docs.x.ai/developers/model-capabilities/text/reasoning

## Definition Of Done

- One command/profile runs the recurring portfolio-and-industry update without mixing in ad hoc deep-research scope.
- Company and industry deep research have explicit independent commands/profiles and do not mutate monitoring/holdings by default.
- The executive update is delta-first, cites material claims, includes portfolio industries, and has no repeated generic paragraphs across holdings.
- Full evidence remains available without visible or hidden mid-sentence truncation.
- Every material factual claim is source-linked and labeled by verification state.
- Grok/X output includes dated post links/handles and is labeled social or speculative until verified.
- Quality checks catch cross-report boilerplate, cross-run stale reuse, incomplete fragments, source failures, and shallow decision usefulness.
- Final-output evaluation and reader feedback feed reflection before memory proposals are finalized.
- A fresh end-to-end run passes deterministic tests, golden report evaluation, manual reader review, and the post-synthesis learning checks.
- The automation is resumed only after the new recurring profile passes the rollout gate.

## Prioritized Backlog

### P0 - Establish The Correct Product And Failure Baseline

These items block other implementation because the current tests certify poor output as good.

#### P0.1 Freeze Characterization Fixtures

- [x] Use `2026-07-04_weekly` as a known-bad reader-output fixture without treating its investment claims as current facts.
- [x] Capture the 12-report cross-file boilerplate repetitions as failing tests.
- [x] Capture known incomplete fragments and hidden-truncation patterns as failing tests.
- [x] Capture the mismatch `quality findings = 0` versus reader defects as a regression case.
- [x] Select 2 earlier evidence-rich Grok/Exa excerpts as positive fixtures.
- [x] Record a small human rubric and expected verdict for each fixture.

Acceptance:

- Existing poor reports fail the new characterization suite for the right reasons.
- Useful evidence-rich examples retain their source content and pass the positive rubric.

Audit correction (2026-08-16): the initial implementation caught the real July corpus when run against it, but its committed fixtures were synthetic and its rubric was declarative. P0.1a below replaced those weak tests and closed this gap.

#### P0.1a Make The Test Suite Credible

- [x] Freeze sanitized excerpts and the prior zero-finding artifact from the actual 12-report `2026-07-04_weekly` run; do not merely copy the ticker names into a synthetic corpus.
- [x] Replace placeholder positive fixtures with sanitized, source-linked excerpts from real strong Grok/Exa outputs.
- [x] Turn the six-dimension reader rubric into an executable evaluation contract with expected per-fixture outcomes and reasons.
- [x] Add near-duplicate/paraphrased boilerplate cases; retain exact matching as a cheap deterministic first gate.
- [x] Replace the active 1,700-word minimum and keyword-presence depth checks; delete the golden-test padding that repeats one sentence 260 times.
- [x] Add state snapshot tests proving research-only routing leaves existing holdings, monitoring, rejected, strategy, and company files byte-for-byte unchanged.
- [x] Enforce profile write permissions in downstream writers and test rejected writes there, not only against the standalone helper.
- [x] Add xAI negative-path tests for no approved fallback, invalid model catalogs, CLI failure, and preservation of required response sections from a recorded response shape.
- [x] Make a clean documented test environment run the entire suite, and add an automated CI test job so collection failures cannot be overlooked.

Acceptance:

- Tests fail for realistic shallow, padded, paraphrased, truncated, unsafe-state, and provider-drift regressions.
- Positive fixtures are real and source-grounded rather than synthetic prose that merely satisfies structural checks.
- A clean install runs the full suite with zero collection errors, and the same command is enforced automatically.

#### P0.2 Define Research Profiles And State Boundaries

- [x] Add an importable `ResearchProfile`/run-spec contract for `portfolio_update`, `company_deep_research`, `industry_deep_research`, and `candidate_discovery`.
- [x] Make scope, time window, provider lanes, depth, output contract, materiality rules, and write permissions explicit in the profile.
- [x] Keep CLI commands as thin wrappers around the shared functions.
- [x] Stop generic company research from adding a stock to monitoring unless the user explicitly requests a status change.
- [x] Keep compatibility routing for existing commands until migration is complete.

Acceptance:

- A research-only request cannot silently change portfolio/watchlist membership.
- Recurring and deep workflows share provider functions but produce distinct manifests and reports.

#### P0.3 Resolve Grok Model Routing Safely

- [x] Add a read-only authenticated model-availability check for xAI.
- [x] Confirm the user's account exposes `grok-4.6` directly.
- [x] Update config, provider defaults, manifest fallbacks, tests, and descriptions together.
- [x] Record requested model, resolved model, tool type, reasoning settings, and fallback reason in run artifacts.
- [x] Fail clearly if X-search is unavailable; do not silently route social research through generic web search.
- [x] Smoke-test stock and industry `x_search` with citations before enabling the model in automation.

Acceptance:

- Every xAI artifact proves which model and tool actually ran.
- X citations and required structured sections survive the migration.

#### P0.4 Stop Evidence Loss And Hidden Truncation

- [x] Separate full evidence text from compact display excerpts in the evidence schema.
- [x] Remove destructive 800/1,000/4,000-character shortening from canonical claim evidence, or store explicit full-text references plus safe complete excerpts.
- [x] Never turn `...` into `.` as a truncation repair.
- [x] Make downstream specialists retrieve the full selected source/raw section when a claim is promoted into a final report.
- [x] Add complete-sentence validation for bullets, table cells, and generated prose.
- [x] Add maximum-context safeguards through evidence selection/ranking, not destructive text clipping.

Acceptance:

- No reader report contains a source fragment cut mid-sentence.
- Every shortened display excerpt links to the preserved full evidence.

#### P0.5 Define Recurring Portfolio Scope And Industry Mapping

- [x] Keep repo CSVs as recurring portfolio membership scope and document the Sheet as intake only.
- [x] Keep v1 impact membership-based without portfolio weights; do not store broker credentials/account data, and leave approximate weights as a later explicit product decision.
- [x] Add or derive stable sector/industry/theme tags for each holding and monitored stock.
- [x] Define the portfolio-industry set used by recurring runs, including deduplication of overlapping themes.
- [x] Add a derived freshness status so CSV metadata is not mistaken for live provider coverage.

Acceptance:

- The recurring manifest can explain exactly which companies and industries it covers and why.
- Portfolio membership and idea intake cannot be confused.

Completion update (2026-08-16): the current 12 tracked companies map to five deduplicated portfolio-industry clusters. A deterministic manifest creates five Exa and five Grok 4.6 X cluster tasks, defers all 12 generic Grok web tasks, records explicit freshness/provider roles/membership-only impact, and refuses to use the latest generated run as an accepted baseline. The synthesis-pack contract truthfully treats Grok web as optional. The full suite passes 299/299.

### P1 - Improve Raw Research Quality And Recurring Update Logic

#### P1.1 Add Change Detection And Materiality

- [x] Define the `last accepted run` pointer separately from the latest generated run.
- [ ] Build deterministic deltas for news, filings, financial metrics, X narratives/accounts, risks, and thesis checkpoints.
- [ ] Classify changes as material, notable, background, duplicate, or stale.
- [ ] Require evidence for `no material change` so silence is not confused with failed coverage.
- [ ] Trigger full company synthesis only for material changes, unresolved high-risk gaps, or explicit user request.
- [ ] Preserve a bounded comparison window so a repeated two-week run does not re-explain the entire company history.

Acceptance:

- The recurring report answers `what changed since the last accepted update?` before restating background.
- Unchanged holdings do not receive padded long reports.

#### P1.2 Improve Exa Research Selection

- [x] Add explicit publication windows to recurring company and industry news searches.
- [ ] Split searches by intent where helpful: official/IR/filing, reputable news, industry/trade press, analyst/context.
- [ ] Rank results by materiality, source tier, recency, company identity, and diversity before contents extraction.
- [ ] Deduplicate syndicated copies of the same release or story.
- [ ] Choose contents URLs by materiality and source diversity instead of first-result order.
- [ ] Persist rejected/low-value source reasons for provider evaluation.
- [ ] Use Exa company/industry search for broad context and candidate discovery, not as unverified numeric truth.

Acceptance:

- High-impact claims prefer primary or high-quality sources.
- The contents budget is spent on distinct material sources.

#### P1.3 Improve Grok/X Research Selection

- [ ] Keep open X discovery plus optional expert-handle seeds; do not hard-filter only to known accounts.
- [ ] Require post URLs, dates, handles, claim text, account/source-quality notes, and whether the claim is new versus the prior run.
- [ ] Separate facts people discuss, community consensus, expert disagreement, rumor, hype, and research leads.
- [ ] Deduplicate repeated accounts/posts and coordinated/copied narratives.
- [ ] Score account usefulness based on repeated verified value and explicit user feedback, not follower count alone.
- [ ] Route factual claims from Grok/X into Exa/filing/IR/financial verification tasks before final thesis use.
- [x] Make generic Grok web deep dives optional or gap-triggered; prioritize Grok's X-native advantage.

Acceptance:

- The X section surfaces real expert/community edge with clickable evidence and clear verification status.
- Social narrative cannot be mislabeled as source-backed fact.

#### P1.4 Build Portfolio-Industry Coverage

- [x] Group holdings into portfolio-relevant industries/themes from durable tags.
- [x] Run one focused Exa industry/news lane and one Grok/X industry pulse per material cluster, not duplicate broad searches per company.
- [ ] Add cross-company read-throughs: shared customers, suppliers, competitors, regulation, capex cycles, and demand signals.
- [x] Highlight concentration and correlated risks when portfolio weights are available; otherwise state that impact is membership-based only.
- [ ] Decide whether broad candidate discovery stays in this run or moves to a separate cadence.

Acceptance:

- The executive report contains an evidence-backed industry section tied directly to portfolio holdings.

### P1 - Rebuild The Reader Report Pipeline

#### P1.5 Create Bounded Synthesis Inputs

- [ ] Build a per-company delta packet containing only selected full evidence, prior thesis/checkpoints, verified changes, X narrative changes, conflicts, and source links.
- [ ] Build one portfolio-industry aggregation packet from company deltas and industry research.
- [ ] Exclude formatter boilerplate and repeated audit statuses from synthesis inputs.
- [ ] Enforce a context budget by ranking evidence, not by clipping sentences.
- [ ] Record selected and omitted evidence with reasons for auditability.

Acceptance:

- A company writer can reason deeply without reading every raw artifact in the whole run.
- The executive writer receives completed company deltas, not 12 raw report stacks.

#### P1.6 Separate Company Writers From Portfolio Editor

- [ ] Generate each material-change company report in an isolated context or bounded task.
- [ ] Generate short delta cards deterministically or with a bounded writer for unchanged/low-change holdings.
- [ ] Aggregate completed company results and portfolio-industry evidence into one executive report.
- [ ] Run an editorial pass that removes cross-company boilerplate and keeps only company-specific next checks.
- [ ] Make the executive report the undisputed first-read artifact; treat deep reports and audit artifacts as drill-down.
- [ ] Update `docs/HUMAN_USAGE_GUIDE.md`, repo map, descriptions, and automation prompt after the contract is implemented.

Acceptance:

- No generic paragraph appears across most company reports unless it is a short global guardrail placed once in the executive report.
- Every company next check names a company-specific claim, event, metric, source, or date.

#### P1.7 Replace Word-Count Quality With Usefulness Gates

- [x] Remove the universal 1,700-word floor for recurring reports.
- [ ] Add separate coverage rules for recurring delta cards, material-change reports, company deep research, and industry deep research.
- [x] Detect cross-report exact and semantic boilerplate.
- [ ] Detect cross-run stale claim reuse when no new source supports it.
- [x] Detect incomplete fragments beyond the previously narrow suffix regex, including bullets and table cells; keep extending historical probes when new patterns appear.
- [ ] Validate every material claim's source link, source tier, date, identity, and verification label.
- [ ] Check that the executive report covers portfolio industries and top attention items.
- [x] Add an executable first reader-value rubric covering material change, specificity, source quality, X insight, reader efficiency, and completeness; extend it with explicit feedback in P1.10.
- [ ] Add a bounded editorial reviewer that can fail the run but cannot invent facts.

Acceptance:

- The 2026-07-04 reports fail for cross-report boilerplate and incomplete excerpts.
- A shorter high-signal recurring update can pass without padding.

### P1 - Make Learning Evaluate The Final Product

#### P1.8 Correct Run Ordering

- [ ] Split finalization into deterministic pre-synthesis readiness and post-synthesis evaluation.
- [ ] Write final reader artifacts before final quality/reflection status is declared complete.
- [ ] Rerun quality, reflection, recurring-failure detection, and memory-draft generation after final reports and repairs.
- [ ] Make automation status reflect final reader output, not only provider packet validity.

Acceptance:

- A final report defect appears in reflection and can create a reviewable memory proposal.

#### P1.9 Add Lightweight Reader Feedback

- [ ] Add a small structured feedback artifact keyed by run id and report path.
- [ ] Support simple chat inputs such as `useful`, `not useful`, `too repetitive`, `too long`, `missed source`, `wrong emphasis`, or free text.
- [ ] Let one feedback item reference a provider lane, source/account, report section, or claim when known.
- [ ] Summarize feedback in the next relevant synthesis context.
- [ ] Require repeated evidence or explicit user confirmation before promoting a broad behavior change into operational memory.
- [ ] Keep company facts in company files and operational lessons in `agents/memory/`.

Acceptance:

- The next relevant run can show which prior feedback changed source selection, research, or writing.
- One dislike does not globally suppress a source without review.

#### P1.10 Measure Provider And Report Yield

- [ ] Track per provider/task: cost, latency, freshness, unique material claims, sources selected, claims verified, claims used in final output, and reader feedback.
- [ ] Track Grok/X handles/posts that repeatedly produce verified insight versus noise.
- [ ] Track Exa domains/results that repeatedly yield primary or high-value evidence versus duplicate/low-value pages.
- [ ] Track report novelty, boilerplate ratio, source coverage, and material-change coverage.
- [ ] Include these metrics in post-run reflection and the memory-evaluation pack.

Acceptance:

- Provider routing can improve from observed yield, not intuition alone.

### P2 - Complete On-Demand Deep Research

#### P2.1 Company Deep-Research Profile

- [ ] Implement the company deep-research manifest and importable runner.
- [ ] Accept a natural-language question plus ticker/company identity and optional time horizon.
- [ ] Run broader company, industry, filing, financial, Exa contents, and Grok/X lanes than the recurring update.
- [ ] Use the same evidence and verification contracts as recurring work.
- [ ] Write one canonical deep report and a concise chat handoff.
- [ ] Ask separately before adding to monitoring or changing thesis/status.

Acceptance:

- A user can ask for a deep company report without running all holdings or mutating state.

#### P2.2 Industry Deep-Research Profile

- [ ] Extend the current manual market-research flow beyond three discovery tasks.
- [ ] Add source-ranked Exa contents, portfolio/company read-through, financial/filing verification for top candidates, and a final first-principles industry report.
- [ ] Keep candidate discovery and verification statuses explicit.
- [ ] Reuse the candidate-review bridge for promotion decisions.

Acceptance:

- A user can request a deep industry report that is materially richer than a discovery list and does not require the recurring portfolio run.

#### P2.3 Natural-Language Routing

- [ ] Route requests by intent: update existing portfolio, research-only company, industry/theme deep research, candidate discovery, or explicit status change.
- [ ] Preserve original user wording and explicit requested output depth.
- [ ] Make ambiguous state-changing requests reviewable instead of defaulting to monitoring insertion.
- [ ] Add examples and tests for common chat prompts.

Acceptance:

- The same ticker can be researched in chat, deeply researched, monitored, bought, or rejected through distinct explicit intents.

### P2 - Source Preferences And Expert Network

#### P2.4 Curated X Expert Seeds

- [ ] Define a durable, non-secret source-preference format by industry/company/theme.
- [ ] Let the user seed handles they already trusts without providing account credentials.
- [ ] Track why a handle is useful, its specialty, and last verified useful contribution.
- [ ] Use seeds as one lane alongside open discovery so new experts can surface.
- [ ] Add review/deprecation rules for promotional, stale, or repeatedly wrong accounts.

Acceptance:

- The system increasingly resembles the user's high-signal X feed without becoming a closed echo chamber.

### P3 - Rollout, Automation, Cost, And Maintenance

#### P3.1 Golden Comparison

- [ ] Run the new pipeline against preserved evidence from at least one prior run.
- [ ] Compare old and new executive reports using the human rubric.
- [ ] Verify that raw insight is preserved while repeated/stale content is reduced.
- [ ] Review one material-change and one no-material-change holding.
- [ ] Review one portfolio-industry section.

#### P3.2 Fresh End-To-End Pilot

- [ ] Run a fresh provider/analysis pilot with the new Grok model and revised Exa selection.
- [ ] Verify source identities, dates, citations, model resolution, and costs.
- [ ] Produce the executive update and only triggered deep reports.
- [ ] Run post-synthesis quality/reflection/memory evaluation.
- [ ] Obtain explicit user acceptance before resuming automation.

#### P3.3 Automation Migration

- [ ] Keep the existing automation paused during implementation.
- [ ] Update the automation to call the recurring portfolio-update profile, not the overloaded legacy contract.
- [ ] Preserve the local Codex-supervised cost boundary unless the user explicitly selects autonomous API mode.
- [ ] Update exact exec-policy rules and validate them.
- [ ] Add clear failure reporting for provider coverage, missing final artifacts, and learning-loop failures.
- [ ] Resume the biweekly schedule only after the pilot passes.

#### P3.4 Documentation And Cleanup

- [ ] Resolve contradictory definitions of the primary report across usage guide, repo map, workflow descriptions, and operational memory.
- [ ] Update README/SETUP after commands or configuration change.
- [ ] Deprecate obsolete final-report assumptions instead of leaving conflicting instructions active.
- [ ] Keep legacy `run-weekly` as a documented compatibility wrapper until safely removed.
- [ ] Apply artifact hygiene only after knowledge promotion and user-review links are safe.

## Recommended Implementation Order

1. P0.1 failure fixtures and reader rubric.
2. P0.2 research-profile/state-boundary contract.
3. P0.3 supported Grok model resolution and smoke test.
4. P0.1a test credibility hardening. (complete)
5. P0.4 evidence preservation/truncation fixes. (complete)
6. P0.5 portfolio-industry source-of-truth contract.
7. P1.1-P1.4 change detection and provider/industry research quality.
8. P1.5-P1.7 bounded synthesis and final report quality.
9. P1.8-P1.10 final-output learning and feedback.
10. P2 company/industry deep-research profiles and routing.
11. P3 golden comparison, fresh pilot, automation migration, and documentation cleanup.

## Verification Plan

- Unit tests for profiles, routing, evidence selection, source ranking, full-text preservation, materiality, and run ordering.
- Golden tests over known-good and known-bad historical reports.
- Cross-file and cross-run report-quality tests.
- Provider contract tests with recorded responses; live smoke tests only for final model/tool compatibility.
- `python -m stock_research validate` and `python -m stock_research memory validate` after structural changes.
- Focused tests first, then the full suite using a repo-local writable `--basetemp` if Windows temp permissions require it.
- Manual reader review of the executive update and one deep report before automation resumes.

Current P0.1-P0.3 result (2026-08-16):

- 37 targeted tests passed; Python compilation, repo validation, operational-memory validation, and isolated model/manifest assertions passed.
- Authenticated xAI model discovery resolved `grok-4.6` without fallback; bounded stock and industry X Search smokes returned cited X sources with provenance and no packet unknowns.
- The historical `2026-07-04_weekly` corpus now yields 36 reader-quality findings instead of the prior false-clean zero.
- At the P0.1-P0.3 checkpoint, the full suite stopped after 187 tests with 5 import errors because the declared `openai-agents` dependency was not visible in that environment. P0.1a resolved this gap; see the completed result below.
- Repo validation also reports an unrelated expired rejected-company cooldown that permits that candidate to be reviewed again.

Current P0.1a-P0.4 result (2026-08-16):

- Full declared-dependency suite: 289 tests passed with zero collection errors; `.github/workflows/tests.yml` enforces the same command on Windows/Python 3.13.
- Focused report/provider/routing checks passed, including realistic historical fixtures, executable positive rubrics, Grok catalog/CLI failures, recorded Grok 4.6 sections, protected-state snapshots, and denied writer permissions.
- Rechecking the full `2026-07-04_weekly` reports now completes in under two seconds locally and returns 53 findings: 25 exact boilerplate, 3 near-boilerplate, 14 per-file human-report defects, and 11 reader-value completeness failures.
- Exa/Grok canonical claims preserve complete selected text, packet summaries expose bounded complete-sentence excerpts, and `load_claim_evidence` retrieves one selected full claim on demand.

## Major Risks

- Model drift: xAI model names and tool support are time-sensitive; resolve and record them at runtime.
- Context overload: preserving full evidence does not mean placing all evidence in one prompt; ranking and bounded packets are required.
- False learning: model-generated preferences can reinforce errors; prioritize explicit user feedback and repeated verified outcomes.
- Source echo chambers: curated expert handles should seed, not replace, open discovery and verification.
- Report overcompression: delta-first does not mean omitting material background needed to understand a change.
- State mutation: research intent and portfolio/watchlist changes must remain separate.
- Cost growth: deeper provider work should be triggered by materiality and user intent, with measured yield.
- Dirty worktree: preserve existing user/run changes and avoid broad staging or cleanup.

## Next Slice

Implement P0.5 portfolio/industry source of truth. User decisions still needed where they materially change the contract:

- the recurring executive-report shape and desired reading time;
- whether full company reports should be materiality-triggered by default;
- whether portfolio weights should be stored;
- whether broad discovery stays in the recurring automation;
- the correct xAI target after authenticated model availability is checked.
