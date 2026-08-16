# Evaluation Metrics

Last updated: 2026-05-18

Run-quality memory for weekly/manual runs and future post-run reflection.

## Metrics To Capture Per Run

- run_id
- run_type: weekly | manual | smoke_test
- start_time and end_time
- deterministic tasks planned
- deterministic tasks completed
- provider tasks planned/completed/failed
- analysis tasks planned/completed/failed
- evidence packets created
- quality issues found
- missing citations
- provider conflicts preserved
- false-positive alerts
- stale data fixed
- file updates made
- human review items created
- user corrections received
- memory items added/updated/deprecated
- SDK agent/tool/LLM metrics
- operational memory ids injected into agent context
- operational memory ids reported by final structured output

## Current Baseline

- id: eval-2026-05-03-provider-smoke-tests
- date: 2026-05-03
- type: evaluation
- scope: provider
- status: active
- confidence: high
- trigger/source: Provider implementation smoke tests.
- lesson: SEC, yfinance, Exa, xAI/Grok, FMP, Polygon/Massive, Alpha Vantage, and financial comparison have live or deterministic smoke-test artifacts. Future evaluation should treat these as baseline provider-path checks, not as investment research conclusions.
- use_when: Verifying provider regressions and planning first full weekly run.
- do_not_use_when: Making investment decisions.
- evidence: `agents/runs/2026-05-09_weekly/evidence_packets/`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-01

- id: eval-2026-05-04-learning-loop-pending
- date: 2026-05-04
- type: evaluation
- scope: global
- status: needs_review
- confidence: high
- trigger/source: User asked whether missing memory automation is recorded.
- lesson: The memory layer supports deterministic read/write/review flows, scheduled invocation, prompt-ready task context, initial SDK prompt injection, and SDK telemetry for injected/reported memory ids. Still pending: full specialist coverage, evaluating whether reported memory ids were used correctly, and feeding telemetry into reflection.
- use_when: Planning Priority 6 orchestration or Priority 7 learning-loop work.
- do_not_use_when: Treating the memory system as already fully autonomous.
- evidence: `docs/plans/investment_agent_backlog.md`, `docs/descriptions/agent_memory_workflow.md`, `stock_research/memory.py`, `stock_research/agent_runtime/tracing.py`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-01

## Post-Run Reflection Checklist

After a weekly or manual run:

- Which provider calls failed or produced low-value output?
- Which evidence packets lacked enough source metadata?
- Which claims were contradicted by another provider?
- Which alerts were noisy or too vague?
- Which file updates needed human correction?
- Which prompt/tool pattern worked well enough to reuse?
- Which memory item should be added, updated, superseded, or deprecated?

## Pending Automation

- Evaluate whether final-output reported memory ids were used correctly, not merely listed.
- Feed SDK local telemetry into post-run memory reflection.

## Recurring Failure Patterns

- No recurring full-run failure patterns recorded yet.
- Direct X.com API path was a corrected provider-routing mistake and is now tracked in `deprecated_memory.md` and `orchestrator_lessons.md`.

- id: eval-2026-05-04-memory-writer-commands
- date: 2026-05-04
- type: evaluation
- scope: global
- status: active
- confidence: high
- trigger/source: deterministic memory writer implementation
- lesson: Deterministic memory add and deprecate commands are implemented. Future memory writes should prefer these commands over manual Markdown edits when adding or deprecating structured memory items.
- use_when: Adding or deprecating operational memory items from Codex, future reflection steps, or future memory writer agents.
- do_not_use_when: Editing prose-only documentation or making complex memory refactors that need human review.
- evidence: `stock_research/memory.py`, `stock_research/cli.py`, `tests/test_memory.py`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-01

- id: eval-2026-05-04-reflect-run-command
- date: 2026-05-04
- type: evaluation
- scope: global
- status: active
- confidence: high
- trigger/source: deterministic post-run reflection implementation
- lesson: Deterministic post-run reflection and memory update proposal generation are implemented through `python -m stock_research memory reflect-run --run-id RUN_ID [--write]`. It writes memory_reflection.json and memory_reflection.md when requested; proposals are not applied automatically.
- use_when: Reviewing weekly/manual runs, generating memory update proposals, or planning the memory and evaluation sub-orchestrator.
- do_not_use_when: Assuming the orchestrator already invokes reflection automatically after every run.
- evidence: `stock_research/memory_reflection.py`, `stock_research/cli.py`, `tests/test_memory_reflection.py`, `agents/runs/2026-05-09_weekly/memory_reflection.md`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-01

- id: eval-2026-05-04-recurring-failure-command
- date: 2026-05-04
- type: evaluation
- scope: global
- status: active
- confidence: high
- trigger/source: deterministic recurring failure detection implementation
- lesson: Recurring failure detection is implemented through `python -m stock_research memory recurring-failures [--write]`. It scans memory_reflection.json artifacts across runs and proposes memory updates when issue categories recur across at least the configured threshold of distinct runs.
- use_when: Reviewing repeated run-quality problems, provider failures, missing artifacts, or recurring workflow issues across weekly/manual runs.
- do_not_use_when: Treating a single-run issue as recurring without enough reflected runs.
- evidence: `stock_research/memory_reflection.py`, `stock_research/cli.py`, `tests/test_memory_reflection.py`, `agents/memory/recurring_failures.md`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-01

- id: eval-2026-05-04-deterministic-run-finalization-is-implemented-th
- date: 2026-05-04
- type: evaluation
- scope: global
- status: active
- confidence: high
- trigger/source: deterministic run finalization implementation
- lesson: Deterministic run finalization is implemented through python -m stock_research memory finalize-run --run-id RUN_ID. It writes memory reflection artifacts, recurring failure reports, and run finalization artifacts in one command for future scheduler/orchestrator use.
- use_when: Ending a weekly/manual run, preparing scheduler integration, or reviewing whether run-learning artifacts are complete.
- do_not_use_when: Assuming memory update proposals are applied automatically or that the scheduler already invokes finalization.
- evidence: stock_research/run_finalization.py, stock_research/cli.py, tests/test_memory_reflection.py, agents/runs/2026-05-09_weekly/finalization.md
- owner: memory and evaluation orchestrator
- next_review: 2026-06-01

- id: eval-2026-05-05-bounded-memory-writer-review
- date: 2026-05-05
- type: evaluation
- scope: global
- status: active
- confidence: high
- trigger/source: bounded LLM memory writer implementation and smoke test
- lesson: Bounded memory writer review is implemented through `python -m stock_research memory writer-review --run-id RUN_ID [--execute] [--write] [--update-drafts]`. It can refine draft memory items, but it does not write operational memory directly; approved writes still go through `memory apply-updates`.
- use_when: Reviewing post-run memory update drafts, planning learning-loop orchestration, or deciding how LLM assistance may touch operational memory.
- do_not_use_when: Assuming the scheduler/orchestrator already invokes writer review automatically or bypassing deterministic schema validation.
- evidence: `stock_research/memory_llm_writer.py`, `tests/test_memory_llm_writer.py`, `docs/descriptions/llm_memory_writer.md`, `agents/runs/2026-05-09_weekly/memory_writer_review.md`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-01

- id: eval-2026-05-05-deterministic-weekly-runner
- date: 2026-05-05
- type: evaluation
- scope: orchestrator
- status: active
- confidence: high
- trigger/source: deterministic scheduled runner implementation
- lesson: `python -m stock_research run-weekly` is the deterministic weekly workflow wrapper. It reaches the framework decision boundary by chaining manifest, provider tasks, analysis tasks, run summary, quality report, memory finalization, bounded memory-writer review, and orchestration report.
- use_when: Running weekly/manual-equivalent deterministic workflow, validating the pipeline before LLM orchestration, or deciding what remains before framework selection.
- do_not_use_when: Assuming OS/app scheduling or LLM orchestrator synthesis already exists.
- evidence: `stock_research/scheduled_runner.py`, `tests/test_scheduled_runner.py`, `docs/descriptions/scheduled_runner.md`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-01

- id: eval-2026-05-10-sdk-local-telemetry
- date: 2026-05-10
- type: evaluation
- scope: orchestrator
- status: active
- confidence: high
- trigger/source: SDK local telemetry hook implementation.
- lesson: SDK `run_metrics.md` now captures agent lifecycle, tool calls, LLM calls/usage when available, injected operational memory ids, and final-output reported memory ids. Future reflection should use these metrics to find slow/brittle tools, missing memory usage, repeated tool failures, and specialist output gaps.
- use_when: Building memory/evaluation orchestration, debugging SDK runs, or deciding whether a run produced enough telemetry for learning-loop updates.
- do_not_use_when: Treating metrics as investment evidence; they describe workflow behavior only.
- evidence: `stock_research/agent_runtime/tracing.py`, `stock_research/agent_runtime/runner.py`, `tests/test_agent_runtime.py`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-15

- id: eval-2026-05-10-sdk-telemetry-reflection
- date: 2026-05-10
- type: evaluation
- scope: orchestrator
- status: active
- confidence: high
- trigger/source: Wired SDK run metrics into deterministic memory reflection.
- lesson: Post-run memory reflection should inspect `run_metrics.md` for SDK timeout/error rows, missing metrics when SDK output exists, injected memory ids, reported memory ids, tool-call counts, and LLM-call counts. These telemetry-derived issues should produce reviewable memory proposals rather than staying isolated in runtime artifacts.
- use_when: Reviewing SDK weekly/manual runs, building the memory/evaluation sub-orchestrator, or diagnosing why an SDK run ended blocked or needs_review.
- do_not_use_when: Treating telemetry as investment evidence or as a substitute for provider/company facts.
- evidence: `stock_research/memory_reflection.py`, `tests/test_memory_reflection.py`, `stock_research/agent_runtime/tracing.py`, `docs/descriptions/agent_memory_workflow.md`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-15

- id: eval-2026-05-11-runtime-quality-gate-specificity
- date: 2026-05-11
- type: evaluation
- scope: orchestrator
- status: active
- confidence: high
- trigger/source: AMZN weekly-style run exposed two over-broad SDK quality gates.
- lesson: Runtime quality gates should accept real repo artifact paths as valid proposal evidence references, not only model-returned source ids. Direct trade-language detection should look for actual stock action patterns such as `buy the stock`, `sell shares`, `trim position`, or `position size`, and should not flag ordinary business phrases such as `Sell on Amazon`.
- use_when: Updating SDK output validation, reviewing why an otherwise evidence-backed run became `needs_review`, or adding new source/citation guardrails.
- do_not_use_when: Weakening source requirements; nonexistent paths and unknown source ids should still fail validation.
- evidence: `stock_research/agent_runtime/reports.py`, `tests/test_agent_runtime.py`, `agents/runs/2026-05-16_weekly/orchestration_report.md`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-15

- id: eval-2026-05-11-final-digest-quality-gates
- date: 2026-05-11
- type: evaluation
- scope: orchestrator
- status: active
- confidence: high
- trigger/source: AMZN/AAPL weekly-style run quality review showed the final digest needed explicit evidence links, readable financial formatting, HRQ routing, and deterministic validation.
- lesson: Weekly final digests should expose evidence links for opportunity, financial, company-news, and company-research artifacts; financial values should be human-readable; Grok/X sentiment must be labeled as a social signal; summaries and next actions must avoid direct trade instructions; taxonomy-only provider conflicts should stay watch items instead of high-risk financial conflicts.
- use_when: Building or reviewing final digest, opportunity assessment, run-end reporting, or golden tests for weekly-style company research.
- do_not_use_when: Replacing deeper company-file updates or human review; the digest is a concise review surface, not the durable thesis record.
- evidence: `stock_research/weekly_digest.py`, `stock_research/opportunity_assessment.py`, `stock_research/report_formatting.py`, `stock_research/scheduled_runner.py`, `tests/test_weekly_digest.py`, `tests/test_opportunity_assessment.py`, `agents/runs/2026-05-16_weekly/final_digest.md`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-15

- id: eval-2026-05-12-investor-usefulness-gate
- date: 2026-05-12
- type: evaluation
- scope: orchestrator
- status: active
- confidence: high
- trigger/source: User reviewed AMZN final digest/opportunity report and found it structurally valid but not actionable or insight-rich.
- lesson: Investor-facing reports must not collapse provider artifacts into status labels, source counts, or internal workflow chores. Final digest, opportunity, and market-research reports must surface concrete news claims, Grok/X community pulse, recurring bull and bear narratives, notable accounts/posts, hype/noise, verified-vs-social/speculative separation, non-obvious/under-discussed insights, valuation/analyst target context where available, peer/candidate context, a decision table, and clear research questions. `quality_findings: []` is not enough unless usefulness gates are also covered.
- use_when: Reviewing final digests, opportunity assessments, sentiment specialists, market discovery reports, prompt quality, or golden tests.
- do_not_use_when: Raw provider smoke tests or low-level schema validation where investor readability is not the output goal.
- evidence: `docs/scratchpads/openai_agents_sdk_orchestration_scratchpad.md`, `docs/plans/investment_agent_backlog.md`, `docs/plans/openai_agents_sdk_orchestration_backlog.md`, `stock_research/opportunity_assessment.py`, `stock_research/weekly_digest.py`, `stock_research/market_research_runner.py`, `tests/test_opportunity_assessment.py`, `tests/test_market_research_runner.py`, `agents/specialists/prompts/sentiment.md`, `agents/runs/2026-05-16_weekly/final_digest.md`, `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/AMZN_opportunity_assessment.md`, `agents/runs/2026-05-10_manual-market-energy-storage/market_research/grid_scale_energy_storage_manual_market_research.md`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-15

- id: eval-2026-05-12-fresh-grok-market-quality
- date: 2026-05-12
- type: evaluation
- scope: discovery
- status: active
- confidence: high
- trigger/source: Fresh live Grok/X + Exa industry run for `AI semiconductor supply chain and advanced packaging`.
- lesson: Fresh market discovery reports should load full raw Grok artifacts when evidence packet claims are truncated, preserve explicit X pulse, trend evolution, bull and bear narratives, candidate follow-up, investor scorecard, hype/noise/rumors, and verification tasks, and keep Grok-only or rumor-like leads verification-limited. Long provider artifact ids must be compacted with stable hashes so Windows path length does not break evidence packet writes. Broad Grok/X multi-ticker baskets should be grouped into concise thematic review items, not one active HRQ row per ticker; regenerated candidate reviews should supersede stale open rows for the same run.
- use_when: Running or reviewing manual market research, Grok/X discovery, candidate extraction, candidate review, market-report formatting, or provider artifact naming.
- do_not_use_when: Treating Grok/X social lead generation as verified company facts or as permission to add a stock to monitoring without approval-gated verification.
- evidence: `stock_research/providers/exa.py`, `stock_research/providers/xai_grok.py`, `stock_research/market_research_runner.py`, `agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/ai_semiconductor_supply_chain_advanced_packaging_manual_market_research.md`, `agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/candidate_review.md`, `agents/human_review_digest.md`, `tests/test_market_research_runner.py`, `tests/test_exa_provider.py`, `tests/test_xai_grok_provider.py`
- owner: market research sub-orchestrator
- next_review: 2026-06-15

- id: eval-2026-05-13-human-report-format-quality
- date: 2026-05-13
- type: evaluation
- scope: reporting
- status: active
- confidence: high
- trigger/source: User reviewed five human-facing reports and flagged visible truncation, duplicate sections, internal workflow prose, dead-looking source ids, and unclear human-review semantics.
- lesson: Human-facing investor reports must be edited like products, not audit dumps. Do not show visible `...` or `[...]` truncation markers. Do not duplicate sections such as market `Companies Discovered` after a candidate pipeline or opportunity `Financial Snapshot` after valuation. Keep internal workflow/status details in audit sections, not executive reads. Source ids should resolve to clickable URLs or artifact links where possible. Candidate review and HRQ digest must explain what the human can approve, reject, or mark as needing more research and what each approval actually triggers.
- use_when: Formatting market reports, opportunity assessments, final digests, candidate reviews, human-review digests, or adding golden tests for investor-facing output.
- do_not_use_when: Raw JSON artifacts, evidence packets, or low-level provider logs where compact machine-readable status is expected.
- evidence: `stock_research/report_formatting.py`, `stock_research/market_research_runner.py`, `stock_research/opportunity_assessment.py`, `stock_research/weekly_digest.py`, `stock_research/candidate_review.py`, `stock_research/human_review_digest.py`, `agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/ai_semiconductor_supply_chain_advanced_packaging_manual_market_research.md`, `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/AMZN_opportunity_assessment.md`
- owner: reporting quality
- next_review: 2026-06-15

- id: eval-2026-05-13-report-storyline-citation-recency
- date: 2026-05-13
- type: evaluation
- scope: global
- status: active
- confidence: high
- trigger/source: User review of semiconductor market report, HRQ digest, AMZN opportunity report, and weekly final digest on 2026-05-13.
- lesson: Investor-facing reports must rank current, material evidence above stale background; remove inline Grok citation markers unless converted to clickable links; explain verification states in human terms; keep HRQ rows concise with linked evidence; and promote strategic AI ecosystem items such as Anthropic, Claude, Bedrock, Trainium, OpenAI, and Cerebras into company tailwinds when source-backed rather than burying them in generic partner lists.
- use_when: Formatting market reports, opportunity assessments, weekly digests, candidate reviews, human-review digests, Grok/X prompts, and quality gates.
- do_not_use_when: Storing ordinary company facts or raw provider output; those belong in run artifacts or company files.
- evidence: stock_research/market_research_runner.py, stock_research/opportunity_assessment.py, stock_research/weekly_digest.py, stock_research/human_review_digest.py, stock_research/candidate_review.py, agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/ai_semiconductor_supply_chain_advanced_packaging_manual_market_research.md, agents/runs/2026-05-16_weekly/reports/opportunity_assessment/AMZN_opportunity_assessment.md
- owner: Codex
- next_review: 2026-06-13

- id: eval-2026-05-16-readiness-hardening-slice
- date: 2026-05-16
- type: evaluation
- scope: global
- status: active
- confidence: high
- trigger/source: Implemented the final pre-ready workflow hardening slice requested by the user.
- lesson: Ready-to-use hardening now includes guarded artifact archive moves, run-finalization archive proposals, run-end human-review summaries for manual paths, category state updates, thesis/status proposal UX tests, and a human-facing report-quality golden gate for truncation, dead citations, raw dict dumps, duplicate sections, and status-only Grok/X output.
- use_when: Reviewing whether the repo is ready for manual weekly use, planning remaining automation/notification work, or changing archive/category/digest/report-quality behavior.
- do_not_use_when: Assuming notification/email automation or scheduled remote execution is already implemented.
- evidence: stock_research/artifact_hygiene.py, stock_research/run_finalization.py, stock_research/run_end_review.py, stock_research/category_state_updater.py, stock_research/report_quality.py, tests/test_artifact_hygiene.py, tests/test_category_state_updater.py, tests/test_run_end_review.py, tests/test_report_quality_golden.py
- owner: orchestration quality
- next_review: 2026-06-16

- id: eval-2026-05-16-codex-run-status-stabilization
- date: 2026-05-16
- type: evaluation
- scope: orchestrator
- status: active
- confidence: high
- trigger/source: Follow-up review of the first real Codex-supervised automation run over 10 holdings.
- lesson: Open human-review rows are normal asynchronous decisions and should not make the scheduled run or Codex review pack fail when provider execution, analysis execution, deterministic quality, finalization, and digest quality are clean. Metadata-only financial conflicts such as share-class company-name variants and exchange aliases should be partial/watch items, not thesis-blocking `needs_human_review` gates. Reserve `needs_review` for actual execution errors, skipped analysis, quality findings, material financial conflicts, missing coverage, blocked finalization, or SDK/runtime problems.
- use_when: Reviewing scheduled run status, Codex-supervised automation output, financial-review gates, or user confusion about `needs_review`.
- do_not_use_when: Suppressing real material numeric financial conflicts, missing provider coverage, or explicit human approval requirements for stock moves/thesis/strategy changes.
- evidence: stock_research/scheduled_runner.py, stock_research/weekly_digest.py, stock_research/codex_review_pack.py, stock_research/financial_compare.py, stock_research/financial_specialist.py, tests/test_scheduled_runner.py, tests/test_financial_compare.py, tests/test_financial_specialist.py, tests/test_codex_review_pack.py, agents/runs/2026-05-16_weekly/codex_supervised_review.md
- owner: orchestration quality
- next_review: 2026-06-16

- id: eval-2026-05-17-human-report-dedup-gate
- date: 2026-05-17
- type: evaluation
- scope: writer
- status: active
- confidence: medium
- trigger/source: User review of AMBA/KRKNF opportunity reports and Grok PDF comparison on 2026-05-17
- lesson: Human-facing opportunity reports and final digests must be checked for repeated long claims across sections; repeated source-backed, X, table, follow-up, and next-action language makes the report feel like pasted sub-reports even when raw evidence is strong.
- use_when: Before finalizing opportunity assessments, weekly final digests, Codex-supervised reviews, or report-quality gates.
- do_not_use_when: Evaluating raw provider artifacts that are intentionally redundant for traceability.
- evidence: stock_research/report_quality.py; stock_research/opportunity_assessment.py; stock_research/weekly_digest.py; agents/runs/2026-05-16_weekly/quality_report.md; docs/plans/human_report_quality_improvement_plan.md
- owner: report_quality
- next_review: 2026-06-14

- id: eval-2026-05-17-for-human-facing-opportunity-reports-determinist
- date: 2026-05-17
- type: evaluation
- scope: orchestrator
- status: active
- confidence: high
- trigger/source: 2026-05-17 AMBA report-quality comparison
- lesson: For human-facing opportunity reports, deterministic de-duplication is only a gate. The final report should be written from a synthesis pack by Codex app GPT-5.5 high from first principles; deterministic opportunity markdown should remain audit/evidence.
- use_when: Reviewing scheduled run output, opportunity assessment quality, Codex-supervised synthesis, or final digest readability.
- do_not_use_when: Building low-level provider evidence packets or deterministic source/audit checks where prose quality is not the goal.
- evidence: agents/runs/2026-05-17_amba-report-quality/reports/AMBA_report_quality_comparison.md; stock_research/human_synthesis_pack.py
- owner: codex
- next_review: 2026-06-17

- id: eval-2026-05-17-codex-app-final-report-primary
- date: 2026-05-17
- type: evaluation
- scope: orchestrator
- status: active
- confidence: high
- trigger/source: User correction on 2026-05-17 that Codex app is the already-decided final-report writer
- lesson: Codex app GPT-5.5 high is the primary writer for final run-level reviews and per-ticker human reports from synthesis packs. API/OpenRouter GPT-5.5 should be treated only as remote/headless fallback or SDK-debug infrastructure, not as a competing quality route to test before using Codex app.
- use_when: Reviewing Codex-supervised scheduled runs, final digest/report quality, human synthesis packs, or model-routing decisions for final human reports.
- do_not_use_when: Running remote/headless jobs where Codex app supervision is unavailable and an explicit API fallback is requested.
- evidence: docs/descriptions/codex_supervised_workflow.md; stock_research/codex_review_pack.py; stock_research/scheduled_runner.py; agents/runs/2026-05-16_weekly/reports/human_synthesis/AMBA_final_human_report.md
- owner: codex
- next_review: 2026-06-17

- id: eval-2026-05-18-final-report-contract
- date: 2026-05-18
- type: procedural
- scope: writer
- status: active
- confidence: high
- trigger/source: User rejected LPKF/Sivers manual run reports because they used ad hoc report shape instead of established automation final-report workflow.
- lesson: Per-ticker final human reports must follow the accepted AMBA-style final-report contract, including provenance paragraph and required sections, even for manual one-off Codex-supervised research. Do not create side report names or ad hoc formats when the user asks for automation-style research.
- use_when: Writing or quality-checking reports/human_synthesis/*_final_human_report.md for scheduled or manual Codex-supervised stock research runs.
- do_not_use_when: The user explicitly requests a different custom report format or a short ad hoc answer outside the repo workflow.
- evidence: Patched human_synthesis_pack instructions and report_quality final-human-report gate on 2026-05-18; regenerated LPK.DE and SIVE.ST final reports in the same final_human_report targets.
- owner: codex
- next_review: 2026-06-18

- id: eval-2026-05-18-final-report-depth-not-summary
- date: 2026-05-18
- type: evaluation
- scope: writer
- status: active
- confidence: high
- trigger/source: User clarified that final human reports had become superficial summaries and must preserve opportunity-assessment insight depth while removing repetition.
- lesson: Final human reports are not short summaries. They must be at least as insight-rich as opportunity assessments, but reorganized into a clear non-repetitive Codex narrative. Include source-backed developments, market context, X trend and notable accounts, bull/bear social claims, rumors/unverified claims, under-discussed angles, valuation/analyst gaps, decision table or scorecard, thesis changers, and concrete next checks.
- use_when: Writing, reviewing, or quality-gating reports/human_synthesis/*_final_human_report.md for Codex-supervised stock research runs.
- do_not_use_when: The user explicitly asks for a brief executive summary only or a non-repo chat answer.
- evidence: 2026-05-18 LPKF/Sivers final report depth correction; patched human_synthesis_pack instructions and report_quality depth markers.
- owner: codex
- next_review: 2026-06-18

- id: eval-2026-05-18-post-codex-final-report-gate
- date: 2026-05-18
- type: evaluation
- scope: writer
- status: active
- confidence: high
- trigger/source: User challenged that improved LPKF/Sivers reports still had to fit the normal automation workflow and not become orphan artifacts.
- lesson: After Codex writes scheduled or manual per-ticker final human reports, rerun `quality-report --require-final-reports`. The pre-Codex deterministic quality report can pass before final reports exist, but the post-Codex gate must fail missing canonical final reports and orphan final reports, then scan the final reports for depth and formatting defects. The active automation prompt and exec-policy rules must both allow this post-Codex gate.
- use_when: Completing Codex-supervised scheduled runs, manual automation-style stock research, or debugging report files that may have been written outside the canonical workflow.
- do_not_use_when: Running the deterministic pre-Codex phase before Codex has had a chance to write final reports.
- evidence: `stock_research/quality_report.py`, `stock_research/codex_review_pack.py`, `docs/descriptions/codex_supervised_workflow.md`, `docs/descriptions/run_summary_and_quality.md`, `C:\Users\valen\.codex\automations\biweekly-holdings-and-monitoring-research\automation.toml`, `C:\Users\valen\.codex\rules\default.rules`
- owner: codex
- next_review: 2026-06-18

- id: eval-2026-05-24-custom-xai-artifact-names-in-synthesis-packs
- date: 2026-05-24
- type: evaluation
- scope: writer
- status: active
- confidence: high
- trigger/source: 2026-05-24 Sheet full deep-dive synthesis pack initially missed same-run Grok web/X artifacts named sheet_full_xai_web_* and sheet_full_xai_x_*
- lesson: Human synthesis packs must recognize both default x_search/web_search filenames and custom-manifest xai_x/xai_web raw artifact names; otherwise final report inputs can falsely appear to be missing Grok web or X evidence even when provider tasks succeeded.
- use_when: Building, validating, or debugging reports/human_synthesis/*_synthesis_pack.md for manual Sheet, market-research, or custom manifest runs that include xAI/Grok lanes.
- do_not_use_when: A run genuinely has no xAI/Grok provider task or the user explicitly requested no social/web auxiliary evidence.
- evidence: stock_research/human_synthesis_pack.py; tests/test_human_synthesis_pack.py; agents/runs/2026-05-24_sheet-full-deep-dives/reports/human_synthesis/VPG_synthesis_pack.md; agents/runs/2026-05-24_sheet-full-deep-dives/quality_report.md
- owner: Codex
- next_review: 2026-06-24

- id: eval-2026-08-16-cross-report-reader-quality
- date: 2026-08-16
- type: evaluation
- scope: writer
- status: active
- confidence: high
- trigger/source: 2026-07-04 weekly final-report false-clean characterization
- lesson: Final reader reports must be evaluated as a corpus and against executable reader-value dimensions. Use sanitized excerpts and the prior quality artifact from the real bad run, source-linked real positive examples, exact plus bounded near-duplicate detection, and complete-fragment checks. Do not use a universal word-count floor: the historical gate could be passed by padding while useful concise reports failed.
- use_when: Building quality reports, golden tests, final report writers, or deciding whether a reader-facing run is complete.
- do_not_use_when: Judging raw provider packet validity alone or treating a word-count floor as reader usefulness.
- evidence: stock_research/report_characterization.py, stock_research/report_quality.py, stock_research/quality_report.py, tests/fixtures/report_quality/, tests/test_report_characterization.py, tests/test_report_quality_golden.py, agents/runs/2026-07-04_weekly/
- owner: quality workflow
- next_review: 2026-10-16
