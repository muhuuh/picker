# OpenAI Agents SDK Orchestration Scratchpad

> Living scratchpad for the OpenAI Agents SDK runtime decision and implementation.
> Keep entries short and scannable. Do not store secrets.

## Goal

- Build the LLM orchestration runtime on OpenAI Agents SDK.
- Keep deterministic kickoff, provider execution, analysis tasks, memory finalization, and quality checks as the reliable foundation.
- Add composable orchestrator and specialist agents that can be run from scheduled workflows, manual Codex-triggered workflows, or as bounded tools.

## Current Decision

- 2026-05-06: User selected OpenAI Agents SDK as the preferred agent framework.
- 2026-05-06: The framework decision boundary in `run-weekly` should now become an OpenAI Agents SDK integration boundary.
- 2026-05-06: Runtime code should be importable/testable under `stock_research/agent_runtime/`; prompts/specs can live under `agents/orchestrator/` and `agents/specialists/`.
- 2026-05-06: First runtime foundation implemented: dependency, context, outputs, registry, main orchestrator builder, company-news specialist builder, specialist-as-tool composition, prompt/spec folders, repo tools, run config wrapper, trace helpers, tests, and no-model-call smoke CLI.
- 2026-05-06: Added live manual SDK execution with `agent-runtime run --execute --write`. First live output exposed quality issues, then prompt/tools/validator were tightened until the AAPL run completed with no quality findings.
- 2026-05-06: Clarified quality semantics: `quality_findings: []` means deterministic runtime gates passed, not that the investment conclusion is automatically correct. Added stricter checks for source-backed proposals and source artifact paths plus `agent-runtime validate-output`.
- 2026-05-06: Wired SDK synthesis into `run-weekly --write --execute-orchestrator`. Live scheduled test correctly ended `needs_review` because provider/analysis tasks were dry-run while the SDK proposed AAPL updates. This is expected and protects against stale-artifact synthesis being treated as fresh research.
- 2026-05-06: Full fresh scheduled run with `--execute-providers --execute-analysis --execute-orchestrator` completed. Initial attempt exposed duplicate stale packets from prior smoke tests; added generated-artifact cleanup before live provider/analysis execution. Final run had 14 packets, one news review, one financial review, and zero deterministic/SDK findings.
- 2026-05-07: Added deterministic proposal review bridge. `agent-runtime queue-proposals --write --queue-review` validates saved SDK output, writes `orchestrator_update_proposals.md`, and appends duplicate-safe human-review rows. Ran it for AAPL; created HRQ-0002 and HRQ-0003.
- 2026-05-07: Added deterministic approved-proposal writer. `agent-runtime apply-proposal --proposal-id ORP-0001 --write` blocks unless the matching HRQ row is `approved`, validates the target under `stock_tracking/stock_info_files/`, updates the company file source/change logs, and writes `applied_update_proposals.md`.
- 2026-05-07: Formalized tooling boundary after user concern about CLI sprawl. New rule: build core Python functions first; deterministic workflows and SDK tools call functions directly; CLI commands are thin manual/scheduler/debug wrappers only.
- 2026-05-07: Hardened repo/memory SDK tools without adding CLI. Added function-first tools for repo map, run summary, quality report, task-specific memory prompt context, and evidence packet index. Runtime context now keeps task-relevant `memory_item_ids` separate from all `known_memory_item_ids`.
- 2026-05-07: Added guarded provider/analysis SDK function tools without adding CLI. `run_provider_tasks_guarded` and `run_analysis_tasks_guarded` plan by default and block live side effects unless runtime context explicitly disables dry-run and grants the matching execution permission.
- 2026-05-07: Tightened memory selection for SDK/tool/guardrail tasks so future agents load orchestrator lessons alongside provider/source-quality notes.
- 2026-05-10: Added local SDK run telemetry hooks. `run_metrics.md` now records agent lifecycle, tool calls, LLM usage when available, injected operational memory ids, and final-output reported memory ids.
- 2026-05-10: Added SDK timeout/error policy. Manual `agent-runtime run` and scheduled `run-weekly --execute-orchestrator` now accept timeout settings; runtime timeouts/errors produce blocked reviewable artifacts and metrics instead of crashing silently.
- 2026-05-10: Memory reflection now reads SDK `run_metrics.md`, surfaces runtime timeouts/errors/missing metrics, and records injected/reported memory ids in reflection metrics.
- 2026-05-10: Added function-first SDK fanout helper. `stock_research/agent_runtime/fanout.py` runs independent agent tasks concurrently with task-specific memory, per-task timeout, partial-failure preservation, and aggregate metrics. It is not wired into scheduled runs yet.
- 2026-05-10: Added first company-research sub-orchestrator. It registers `company_research_orchestrator`, exposes it to the main orchestrator, builds a one-ticker company research packet with financials/company-news/filings/sentiment/company-search/risk-thesis lanes, runs company-news fanout, and aggregates missing lanes into next-run tasks.
- 2026-05-10: Added SDK financial specialist. It registers `financial_specialist`, injects financial specialist memory, exposes it to main/company-research orchestrators, and runs it in company-research fanout before company-news. Targeted SDK runtime tests pass.
- 2026-05-10: Added SDK xAI/Grok sentiment specialist. It registers `sentiment_specialist`, injects Grok/source-quality and direct-X deprecation memory, exposes it to main/company-research orchestrators, and runs in company-research fanout after company-news.
- 2026-05-10: Added SDK SEC filing specialist. It registers `filing_specialist`, injects SEC/source-quality memory, exposes it to main/company-research orchestrators, and runs in company-research fanout between company-news and sentiment.
- 2026-05-10: Clarified fanout task naming after user concern: `financial_aapl`/similar are per-run task ids generated from the ticker parameter, not AAPL-specific agents. Added generic `company_search_specialist` plus deterministic Exa `company` mode provider tasks for tracked tickers and human stock-research tickers.
- 2026-05-10: Added the remaining generic company-research SDK lanes: `risk_thesis_specialist`, `writer_specialist`, and `quality_reviewer_specialist`. They are prompt/spec/module definitions reusable for any ticker.
- 2026-05-10: Wired company-research fanout into scheduled `run-weekly` for all current-holding and monitoring tickers when SDK orchestration is enabled. The scheduled path writes per-ticker artifacts under `agents/runs/{run_id}/company_research/` before the main orchestrator synthesis.
- 2026-05-10: Added first market-research SDK sub-orchestrator and discovery specialists. Discovery now has explicit Exa industry/company lanes and a required Grok/X lane for niche trends, hype, rumors, sentiment, and emerging ticker leads. Grok leads require Exa/filing/market-data verification before promotion.
- 2026-05-10: Rechecked official xAI X Search docs. Current supported `x_search` controls are `from_date`, `to_date`, `allowed_x_handles`, `excluded_x_handles`, `enable_image_understanding`, and `enable_video_understanding`; allowed and excluded handles are mutually exclusive and capped at 10.
- 2026-05-14: Report-quality root-cause pass after user asked whether AMZN/Amkor fixes were general. Generalized fixes were made in code, not hand-patched per ticker: Exa company evidence now includes entity descriptions/tickers, Exa source ids are suffixed per artifact to avoid collisions, stale prior-year quarter/results/outlook snippets are filtered out of executive/context sections, repeated company-profile snippets are filtered from industry context, Grok candidate heading noise is cleaned at extraction time, company-news/financial specialists cite real provider ids or ticker-specific artifact ids instead of generic placeholders, and report text repair catches mojibake/truncation markers.
- 2026-05-14: Fresh validation artifacts for review: `agents/runs/2026-05-14_manual-market-ai-semiconductor-fresh/market_research/ai_semiconductor_supply_chain_advanced_packaging_fresh_manual_market_research.md`, `agents/runs/2026-05-14_manual-market-ai-semiconductor-fresh/market_research/candidate_review.md`, `agents/human_review_digest.md`, `agents/runs/2026-05-16_weekly/final_digest.md`, `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/AMZN_opportunity_assessment.md`, and `agents/runs/2026-05-16_weekly/company_research/AMZN_company_research.md`.
- 2026-05-14: AMZN company-research packet is complete and source-clean for review. The broader weekly run still has `needs_review` surfaces because AAPL generated provider artifacts are incomplete and open HRQ items remain; this does not block reviewing the AMZN slice.
- 2026-05-14: Rerun gotcha discovered: `run-weekly` recreates generated run artifacts, so rerunning analysis/orchestrator without provider execution on an existing run id can remove provider-dependent artifacts. Add a safer incremental rebuild mode before relying on repeated same-run formatting passes.
- 2026-05-15: User accepted the AMZN opportunity-assessment quality/structure as the target level for now and accepted the final digest as a concise quick-read surface. Clarified that `company_research/{TICKER}_company_research.md` is mostly an internal lane/coverage packet, not a primary human review report.
- 2026-05-15: Human-review UX decision: do not ask the user to approve routine source-backed company-file factual edits. Target behavior is auto-apply low-risk factual edits through a scoped writer and summarize file/section/source changes as FYI; keep thesis/status/strategy/trade-impacting edits approval-gated.
- 2026-05-15: Digest UX fix: hide older duplicate candidate review rows from the human-facing digest when the same category/target appears again from a newer regenerated run. The durable HRQ keeps audit history; the digest should show the newest actionable row.
- 2026-05-15: Added artifact lifecycle/hygiene plan. Long-lived active knowledge should be promoted into stock/market/strategy files and indexed; old non-active run reports should be movable to archive instead of cluttering active research surfaces.
- 2026-05-10: Added clean manual market-research runner. `python -m stock_research market-research run --topic TOPIC --subject-type industry|theme --write [--execute-providers] [--execute-orchestrator]` builds a manual manifest, plans/runs Exa context + Exa company discovery + Grok/X discovery, extracts typed candidate leads, writes a market report, and applies discovery gates for Grok-only leads, rejected cooldowns, source ids, verification labels, and rumor flags.
- 2026-05-10: Live manual provider examples ran for `robotics suppliers in Europe` and `grid scale energy storage`. First robotics run exposed noisy ticker extraction (countries/acronyms); tightened extraction and reran successfully. Energy-storage provider run produced plausible Exa-only and Grok-only candidates.
- 2026-05-10: Live SDK market fanout on `grid scale energy storage` initially exposed a markdown-only artifact gap for JSON evidence packets. Added `load_evidence_packet` repo tool, fixed evidence packet listing subject fields, updated specialist prompts, and reran successfully with status `complete` and no quality findings.
- 2026-05-10: Added manual candidate-review bridge. `market-research candidate-review --run-id RUN_ID --write --queue-review` groups duplicate/share-class candidate leads, writes `market_research/candidate_review.md`, and queues duplicate-safe human-review rows for verification/monitoring decisions without adding stocks to monitoring. Live energy-storage run created CRG-0001..CRG-0006 and HRQ-0004..HRQ-0009.
- 2026-05-11: Clarified discovery lifecycle after user question. Backlog now separates discover, normalize, gate, human review, verify, and promote. Candidate review is lead triage; company research is the deeper verification phase for a specific ticker/company.
- 2026-05-11: Added approved-candidate verification follow-up bridge. `market-research candidate-followup --run-id RUN_ID --review-id HRQ-0004 --write` only processes approved candidate-review rows and writes a candidate verification manifest/plan using existing provider and analysis task shapes. Live energy-storage check correctly returned `no_approved_items` because HRQ-0004..HRQ-0009 are still open.
- 2026-05-11: Added approval-gated candidate promotion writer. `market-research candidate-promote --run-id RUN_ID --review-id HRQ-0004 --write` only writes monitoring CSV/company-file state for approved and verified `monitoring_candidate` rows; live energy-storage check correctly blocked because HRQ-0004 is open, Grok-only/verification-only, and missing verification artifacts.
- 2026-05-11: User asked to make the human-review loop more ergonomic. Added backlog items for an open HRQ digest grouped by decision type/priority and a later Codex/app notification or email automation when new/high-priority review items exist.
- 2026-05-11: Implemented open HRQ digest. `python -m stock_research human-review digest --write` writes `agents/human_review_digest.md`; live queue output grouped 9 open items into company-file updates, Grok/X candidate verification, candidate verification, and strategy/workflow.
- 2026-05-11: Implemented deterministic HRQ decision updater. `python -m stock_research human-review decide --set HRQ-0004=approved --note "Run verification." --write` records explicit user decisions, appends decision notes, refreshes the digest, and intentionally leaves verification/promotion/file writes to separate approval-gated commands.
- 2026-05-11: Approved HRQ-0007 / ADSE for verification-only workflow validation. `candidate-followup` wrote the verification manifest/plan; provider execution completed 7 of 8 lanes, with FMP blocked by subscription/402; analysis execution completed 4 of 4 tasks; `candidate-promote` correctly blocked because HRQ-0007 is `verify_before_monitoring`, not `monitoring_candidate`.
- 2026-05-11: Added `candidate-verification-result` after the live ADSE check showed verification outcomes were too scattered. The consolidated report now records missing provider evidence, specialist statuses, findings, and next actions in `market_research/candidate_verification_result.md`.
- 2026-05-11: Added first portfolio review sub-orchestrator. `portfolio_review_orchestrator` is registered, exposed to the main orchestrator, builds a deterministic packet over current holdings/monitoring/rejected/open HRQ/approved HRQ/candidate verification results, and writes `portfolio_review.md` without trading, moving stocks, or editing company files.
- 2026-05-11: Added first memory/evaluation sub-orchestrator. `memory_evaluation_orchestrator` is registered, exposed to the main orchestrator, builds a deterministic packet over run metrics, quality report, memory reflection, recurring failures, memory update drafts, memory writer review, and finalization, and writes `memory_evaluation.md` without applying memory updates.
- 2026-05-11: Broadened main orchestrator aggregation. `build_orchestrator_input(..., context=...)` now embeds a main aggregation packet covering company research, market research, portfolio review, memory/evaluation, candidate verification results, HRQ digest, and open/approved HRQ counts.
- 2026-05-11: Researched human-in-the-loop best practice and documented the digest-first human review operating model. Decision: `agents/human_review_digest.md` is the user inbox; `agents/human_review_queue.md` is durable state; portfolio/memory/candidate/proposal reports are deeper context. Runs should continue safe independent work while approval-gated branches wait. Email/app notification is a later layer over the digest; email replies should not be treated as approvals until a strict ingestion workflow exists.
- 2026-05-11: Added `docs/HUMAN_USAGE_GUIDE.md` because architecture docs were still too abstract for day-to-day use. The guide explains what the human should type in Codex, where results are written, how to read `agents/human_review_digest.md`, and how to approve/reject HRQ items.
- 2026-05-11: Ran a realistic weekly-style AMZN holding validation. Added AMZN to current holdings, executed providers/analysis, and wrote `agents/runs/2026-05-16_weekly/final_digest.md`.
- 2026-05-11: Added deterministic `opportunity_assessment` analysis and SDK `opportunity_assessment_specialist`. The lane synthesizes financials, news, filings, Exa context, and Grok/X sentiment into a concise expert-opinion report for human review. It is research synthesis only, not a trade instruction.
- 2026-05-11: Added final run digest artifacts: `final_digest.md/json`. The digest is the reliable human-facing research summary when the live SDK main orchestrator is unavailable or too noisy.
- 2026-05-11: Tightened final digest/opportunity output quality after reviewing the real AMZN/AAPL run. Added explicit digest evidence links, digest/opportunity validators, readable financial formatting, Grok/X social-signal checks, direct trade-language blocking, taxonomy-only conflict handling, deduped opportunity news positives, weekly HRQ digest refresh, and golden tests. Refreshed `agents/runs/2026-05-16_weekly/final_digest.md`; status is `ready` with no digest quality findings.
- 2026-05-12: User reviewed the AMZN final digest/opportunity report and correctly flagged a serious product-quality failure: reports were structurally valid but not useful. They exposed status labels (`mixed_social_signal`, `ready_for_company_update`) and internal workflow notes instead of actionable investor insight. Raw Grok output already contained useful X narratives, account references, bullish/bearish claims, hype/noise, and investor implications; the synthesis layer threw most of that away. Fix priority: make Grok/X narrative first-class, remove internal data-quality chores from human-facing risk/watch sections, and require final reports to answer what changed, why it matters, who is saying it, what is verified vs social/speculation, and what research decision follows.
- 2026-05-12: First repair pass implemented. Grok/X prompts now demand investor-grade X pulse, verified facts, bull/bear narratives, accounts/posts, hype/noise, rumors, and implications. Opportunity/final digest synthesis now reads raw Grok output when evidence packets are truncated and surfaces those narratives plus concrete Exa news developments. Regenerated AMZN/AAPL reports are much more useful than the prior status-only output, but still not the final bar; next milestone is a richer investor insight report and golden tests modeled on the user's old Grok PDFs, with a higher target than those PDFs.
- 2026-05-12: Cleaned the repaired AMZN/AAPL reports again after inspection. Human-facing opportunity reports no longer show raw `sentiment_label`; they explain Grok/X as cite-backed social/community evidence. Recommended next action now states a concrete research decision and strips broken/truncated citations from the action and summary.
- 2026-05-12: Added the richer opportunity-report shape. `AMZN_opportunity_assessment.md` now includes `Investor Insight Report` with executive read, company/industry context, thesis/trend changes, expert/community split from X, non-obvious/under-discussed insights, valuation/analyst target snapshot, peer context, decision table, and next research questions. The final digest now also exposes forward P/E and analyst target/upside. Remaining gap: apply the same investor-usefulness bar to market-research/discovery reports and run a fresh live Grok/X pass with the improved prompt.
- 2026-05-12: Applied the same first investor-usefulness pass to manual market-research reports. `grid_scale_energy_storage_manual_market_research.md` now has executive read, industry/theme context, X/community pulse, trend evolution, candidate pipeline, non-obvious/contrarian angles, decision table, and explicit approve/reject/request-more-research wording. Candidate extraction now preserves ticker-specific Grok reasons like FLNC/NRGV/NXXT instead of generic `Grok research completed` text. Remaining quality gap: run fresh live Grok/X with the improved prompts and compare whether the new raw output beats the older stored Grok artifact.
- 2026-05-12: Fresh live Grok/X + Exa industry run for `AI semiconductor supply chain and advanced packaging` exposed two robustness gaps and one report-quality gap. Fixed compact provider packet ids for long run/topic names, made market reports load full raw Grok text when evidence claims are truncated, and added X bull/bear narratives, Grok candidate follow-up, and Grok investor scorecard sections. The regenerated market report surfaces concrete signals around CoWoS/EMIB diversification, Amkor/FORM/LPKF/MKSI/ENTG/ONTO/CAMT/SK Hynix follow-up ideas, hype/noise, and verification tasks. Candidate review queued HRQ-0010..HRQ-0027 and refreshed `agents/human_review_digest.md`.
- 2026-05-11: AMZN quality iteration found an over-strict financial gate. An industry taxonomy disagreement (`Internet Retail` vs `Specialty Retail`) is now classified as `partial_review` / watch item, not a material financial conflict.
- 2026-05-11: Earlier AMZN validation exposed a scheduled main-orchestrator `Connection error`; after API credit was added and validation gates were tightened, the full fresh AMZN/AAPL weekly path completed successfully with no SDK quality findings. Keep deterministic `final_digest.md` as the stable human-facing fallback even when live SDK synthesis succeeds.

## Official Docs Reviewed

- OpenAI Agents SDK overview: https://openai.github.io/openai-agents-python/
- Agents: https://openai.github.io/openai-agents-python/agents/
- Agent orchestration: https://openai.github.io/openai-agents-python/multi_agent/
- Running agents: https://openai.github.io/openai-agents-python/running_agents/
- Tools: https://openai.github.io/openai-agents-python/tools/
- Guardrails: https://openai.github.io/openai-agents-python/guardrails/
- Tracing: https://openai.github.io/openai-agents-python/tracing/
- Sessions: https://openai.github.io/openai-agents-python/sessions/
- Results: https://openai.github.io/openai-agents-python/results/
- Usage: https://openai.github.io/openai-agents-python/usage/
- Models: https://openai.github.io/openai-agents-python/models/
- Context management: https://openai.github.io/openai-agents-python/context/

## Findings

- SDK primitives match this repo: agents, function tools, agents as tools, handoffs, guardrails, sessions, tracing, structured outputs, and usage tracking.
- Use code orchestration for deterministic workflow order, dependency handling, parallel fanout, retries, and cost control.
- Use LLM orchestration for synthesis, prioritization, contradiction detection, and deciding which bounded tools/specialists to call after deterministic inputs exist.
- Use manager-style `Agent.as_tool()` for specialist calls when the main orchestrator should own the final synthesis.
- Use handoffs sparingly, mainly for interactive Codex/user triage where a specialist should own the next conversational turn.
- Use `asyncio.gather` around independent `Runner.run(...)` calls for parallel specialist work, not hidden prompt-only parallelism.
- Use structured outputs through `output_type` for orchestrator decisions, specialist reviews, update proposals, and alert packets.
- Use `RunConfig` for workflow name, trace id, group id, metadata, model defaults, and sensitive-data trace settings.
- Use SDK tracing plus local run artifacts. OpenAI traces are useful, but repo-local `trace_links.md`, run metrics, and finalization artifacts remain the audit surface.
- Use SDK usage tracking and hooks to persist request counts, token usage, model calls, and durations into run metrics.
- Use tool guardrails on custom function tools. Agent-level guardrails only cover workflow boundaries; file/provider tools need their own validation.
- Use SDK sessions for conversation/runtime continuity, not as the durable investment memory. Durable truth stays in repo files and `agents/memory/`.
- Do not put secrets into `RunContextWrapper.context`, traces, sessions, or repo artifacts.
- Task-specific specialist contexts matter: when the main orchestrator exposes the company-news specialist as a tool, build that specialist with `company news specialist` memory rather than reusing only main-orchestrator memory.

## Proposed Runtime Shape

```text
stock_research/agent_runtime/
  __init__.py
  context.py              # run id, repo root, manifest paths, memory context, permissions
  registry.py             # agent/tool registry and construction helpers
  runner.py               # SDK Runner wrappers, async fanout, aggregation, errors
  tracing.py              # trace ids, local metrics, trace_links.md, hooks
  guardrails.py           # source metadata, secret redaction, file-write restrictions
  outputs.py              # Pydantic output contracts for orchestrators/specialists
  tools/
    repo_tools.py         # read repo map, load memory, inspect artifacts
    provider_tools.py     # guarded wrappers around deterministic provider functions
    analysis_tools.py     # guarded wrappers around financial/news analysis functions
    memory_tools.py       # prompt-context, draft/apply flow, human review queue
    writer_tools.py       # proposal-only file updates, scoped by target file
  orchestrators/
    main.py
    company_research.py
    market_research.py
    portfolio_review.py
    memory_evaluation.py
  specialists/
    financial.py
    company_news.py
    grok_sentiment.py
    exa_industry.py
    filing.py
    risk.py
    writer.py

agents/
  orchestrator/
    prompts/
    specs/
  specialists/
    prompts/
    specs/
```

## Workflow Fit

```text
run-weekly
  -> deterministic manifest/provider/analysis/summary/quality/memory finalization
  -> load task-relevant operational memory
  -> OpenAI Agents SDK orchestration runtime
     -> scheduled per-ticker company-research fanout for current/monitoring tickers
     -> manager/orchestrator agent uses specialist agents as tools for bounded synthesis
     -> structured outputs become alerts, update proposals, review queue items, and next-run tasks
  -> quality review
  -> memory reflection and finalization
```

## Key Design Decisions

- Keep existing deterministic tools as first-class Python functions and expose them to agents as function tools.
- Do not make CLI commands the integration layer. SDK tools should wrap Python functions directly, not subprocess CLI calls.
- Treat specialist agents as composable units: callable directly by scheduled code, callable as `Agent.as_tool()` by orchestrators, and usable in deterministic task chains through stable input/output contracts.
- Give every agent run a `run_id`, `task_id`, `agent_id`, `trace_id`, `group_id`, and structured output path.
- Store local observability artifacts even when OpenAI tracing is enabled.
- Keep file writes proposal-first by default. Writer tools may only edit assigned files after validation or explicit workflow permission.

## Open Questions

- Should any future faster Grok tier be safe for low-priority/simple X scans, or should all X-search stay on `grok-4.3` until live outputs prove otherwise?
- Should programmatic Codex SDK/app-agent control ever become part of this repo, or should Codex remain the outside human-supervised automation runner?
- Should sessions use SQLite later for interactive workflows, or should scheduled/manual runs continue to rely only on explicit repo artifacts?
- What additional local trace metrics are worth persisting beyond the current markdown metrics without creating noisy artifacts?

## Next Steps

- Feed selected model/tier into finalization and memory reflection only if it proves useful for cost/quality retrospectives.
- Add provider failure, malformed specialist output, and missing-citation golden tests.
- Add deeper memory-use evaluation beyond injected/reported ids.
- Run 2-3 real manual market-research examples with live providers and inspect whether Exa/Grok prompts surface useful candidate leads.
- Improve candidate extraction beyond ticker regex if live provider output uses company names without tickers.
- Execute an approved candidate verification run after the user approves one HRQ row, then inspect whether the generated provider/analysis evidence is enough for promotion.
- Run `candidate-promote` after a verified `monitoring_candidate` row is approved, then inspect the created monitoring row/company file quality on a real candidate.
- Use the open human-review digest as the source surface for future notification automation, so reminders are concise and actionable rather than a raw table dump.
- Later add Codex/app or email digest notifications; keep email notification-only until strict reply ingestion is designed and tested.
- Run realistic manual and weekly-style examples through final main aggregation and improve prompts where output is too generic.
- Add missing specialist/provider depth only when real runs show a specific quality gap.
- Wire market-research fanout into scheduled `run-weekly` only after validating the manual market-research quality.
- Use the Codex app automation as the first scheduled runner; next automation work is notification/email digest, not more scheduler plumbing.

## Risks / Gotchas

- Traces may include sensitive LLM/tool inputs by default; configure sensitive-data handling deliberately.
- Agent-as-tool currently does not expose tool-guardrail options directly, so guard critical logic inside wrapped function tools or the specialist runner.
- Handoffs transfer conversation control and can make audit boundaries less clear; use them only when that behavior is intentional.
- SDK sessions are convenient but not a substitute for repo memory, evidence packets, or run artifacts.
- Parallel fanout needs explicit timeout/error handling so one slow provider/specialist does not block the whole weekly run.

## Commands / Env Notes

- Future dependency: `openai-agents`.
- Future live runtime env: `OPENAI_API_KEY`.
- Existing prompt memory command for runtime injection: `python -m stock_research memory prompt-context --task TASK`.
- Existing deterministic weekly boundary: `python -m stock_research run-weekly --write`.
- SDK registry smoke command: `python -m stock_research agent-runtime smoke --run-id 2026-05-09_weekly`.
- Live manual SDK command: `python -m stock_research agent-runtime run --run-id 2026-05-09_weekly --execute --write`.
- Live quality iteration found and fixed:
  - bad invented target path `companies/AAPL.md`,
  - missing memory ids,
  - invented memory id `orch-2026-05-03-agent-registry`.
- Current live output status: complete with zero quality findings.
- Saved output validation command: `python -m stock_research agent-runtime validate-output --run-id 2026-05-09_weekly`.
- Current runtime quality gates check summary/status, direct trade wording, valid memory ids, existing file targets, proposal source ids, and source artifact paths.
- Scheduled SDK command: `python -m stock_research run-weekly --write --execute-orchestrator` (API mode only).
- Fresh scheduled SDK command: `python -m stock_research run-weekly --write --execute-providers --execute-analysis --execute-orchestrator` (API mode only).
- Codex app biweekly automation command: `C:\Python313\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis`.
- Codex execpolicy validation command: `codex execpolicy check --pretty --rules C:\Users\valen\.codex\rules\default.rules -- C:\Python313\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis`.
- Codex-supervised run handoff: Python writes `agents/runs/{run_id}/codex_supervised_review_pack.md`; Codex GPT-5.5 high reads it and writes `agents/runs/{run_id}/codex_supervised_review.md`.
- SDK timeout knobs:
  - `python -m stock_research agent-runtime run --run-id RUN_ID --execute --write --timeout-seconds 300`
  - `python -m stock_research run-weekly --write --execute-orchestrator --orchestrator-timeout-seconds 300`
- Freshness behavior: actionable SDK output from dry-run provider/analysis inputs is marked `needs_review`.
- Idempotence behavior: live provider/analysis execution cleans generated run artifacts first, avoiding duplicate stale evidence when rerunning the same run id.
- Proposal bridge command: `python -m stock_research agent-runtime queue-proposals --run-id 2026-05-09_weekly --write --queue-review`.
- Proposal writer command: `python -m stock_research agent-runtime apply-proposal --run-id 2026-05-09_weekly --proposal-id ORP-0001 --write`.
- Current AAPL proposals HRQ-0002 and HRQ-0003 are open, so `apply-proposal --write` should return `blocked` until the user approves them.
- Tooling boundary: prefer `function -> SDK tool/direct workflow -> optional CLI`; do not add CLI commands for small helpers.
- Repo/memory SDK tools now available: `load_repo_map`, `load_run_summary`, `load_quality_report`, `load_memory_prompt_context`, `list_evidence_packets`, `load_run_markdown`, `list_run_markdown_artifacts`, `load_operational_memory`, `load_stock_tracking_csv`.
- Guarded provider/analysis SDK tools now available: `run_provider_tasks_guarded`, `run_analysis_tasks_guarded`.
- Provider/analysis SDK execution guard: live side effects require `execute=True`, `dry_run=False`, and the matching context permission (`execute_providers` or `execute_analysis`).
- Memory selector note: task labels containing `sdk`, `tool`, or `guardrail` now include orchestrator lessons, so guarded-tool implementation lessons are visible during future SDK work.
- Local telemetry note: `LocalRunHooks` records `agent:*`, `llm:*`, `tool:*`, `memory_context:*`, and `memory_output:*` metrics. Metrics intentionally avoid raw prompts/tool input/output.
- Reflection telemetry note: `memory_reflection.py` now treats SDK timeout/error/missing metrics as reflection issues and proposals, so runtime reliability problems feed the learning loop.
- Fanout note: `AgentFanoutTask` and `run_agent_fanout_sync` exist for code-level parallel specialist execution. Scheduled `run-weekly --write --execute-orchestrator` now runs company-research fanout across current-holding and monitoring tickers before the main orchestrator path.
- Company-research dry-run command: `python -m stock_research agent-runtime run --run-id 2026-05-09_weekly --agent-id company_research_orchestrator --task "company research sub-orchestrator" --ticker AAPL`.
- Company-research fanout currently includes `financial_specialist`, `company_news_specialist`, `company_search_specialist`, `filing_specialist`, `sentiment_specialist`, `risk_thesis_specialist`, `opportunity_assessment_specialist`, `writer_specialist`, and `quality_reviewer_specialist`.
- AMZN validation command used for the complete provider/analysis run: `python -m stock_research run-weekly --write --today 2026-05-11 --execute-providers --execute-analysis --execute-orchestrator --orchestrator-timeout-seconds 900`.
- AMZN deterministic digest artifact: `agents/runs/2026-05-16_weekly/final_digest.md`.
- AMZN opportunity report: `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/AMZN_opportunity_assessment.md`.
- AMZN investor-usefulness repair validation: `python -m pytest -q`, `python -m compileall stock_research`, `python -m stock_research memory validate`, `python -m stock_research validate --today 2026-05-12`, and `python -m stock_research agent-runtime validate-output --run-id 2026-05-16_weekly` all passed after regenerating AMZN/AAPL opportunity reports and `final_digest.md`.
- Market investor-usefulness repair validation: `python -m pytest tests/test_market_research_runner.py -q` passed and `grid_scale_energy_storage_manual_market_research.md` was regenerated from existing evidence without live provider calls.
- 2026-05-13 report-quality validation: `python -m pytest tests/test_market_research_runner.py tests/test_human_review_digest.py tests/test_opportunity_assessment.py tests/test_weekly_digest.py` passed (35 tests). Additional grep quality scan over the five reviewed artifacts found no visible `...`, `[...]`, internal `Manual market research setup`, removed duplicate market sections, removed duplicate opportunity `Financial Snapshot`/`Grok/X Community And Sentiment`, and removed the opportunity boilerplate sentence.
- Market discovery grouping repair: candidate review and market reports now group repeated Grok/X multi-ticker basket leads into concise thematic review items instead of one HRQ row per ticker. Regenerated stale rows for the same run are marked `superseded` before new rows are appended.
- Fresh semiconductor validation command: `python -m stock_research market-research run --topic "AI semiconductor supply chain and advanced packaging" --subject-type industry --subject-id ai_semiconductor_supply_chain_advanced_packaging --run-id 2026-05-12_manual-market-ai-semiconductor-supply-chain --write --execute-providers --execute-orchestrator --today 2026-05-12 --timeout-seconds 300`.
- Fresh semiconductor review artifacts to inspect:
  - `agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/ai_semiconductor_supply_chain_advanced_packaging_manual_market_research.md`
  - `agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/candidate_review.md`
  - `agents/human_review_digest.md`
- Fresh semiconductor output judgment: much better and reviewable. The report now surfaces X pulse, trend evolution, bull/bear narratives, concrete Grok scorecard, Exa-backed candidates, thematic Grok baskets, and explicit human decisions. Remaining quality work should focus on stronger golden fixtures and post-approval verification ranking, not rebuilding the core manual market loop.
- 2026-05-13: User reviewed five human-facing outputs and found remaining product-quality issues: visible truncation, duplicated report sections, internal workflow/status prose in executive sections, dead source ids, unclear candidate-review purpose, and unclear HRQ category semantics. Fixed formatter-level visible truncation, removed duplicated market/opportunity sections, made market source ids clickable, clarified candidate-review/human-review digest instructions, moved internal audit/status content below the story, and regenerated the semiconductor market report, candidate review, HRQ digest, AMZN opportunity report, and weekly final digest.
- 2026-05-13: Report-quality judgment after regeneration: good enough for another human review pass, not final ceiling. The market report now has a clearer storyline and clickable sources; AMZN opportunity report no longer duplicates financial/news/Grok sections and no longer renders visible `...`; HRQ digest now explains what each category means and what approval does. Remaining improvement target: stronger golden fixtures for no truncation/no duplicate sections and better candidate basket ranking before verification.
- 2026-05-13: Second user review pass found subtler product-quality gaps: stale background evidence was still able to dominate the market bottom line, inline Grok `[[1]]` citations created dead-looking references outside the source list, HRQ rows exposed source-id walls instead of linked evidence, and AMZN strategic AI ecosystem value (Anthropic/Claude/Bedrock/Trainium/OpenAI/Cerebras) was present in evidence but not promoted into the thesis. Fixed market recency/context ranking, richer X pulse extraction, decision-table wording, dead citation cleanup, HRQ evidence links, candidate-review HRQ explanation, stronger Grok industry prompt density, weekly digest citation cleanup, and AMZN strategic AI extraction.
- 2026-05-13: Follow-up quality pass after user clarification: AMZN/AAPL opportunity outputs now synthesize provider excerpts into investor statements instead of dumping raw chunks, market bottom line no longer repeats the same X thesis in every row, stale Amkor Q4 2025 evidence is limited to the source list, and text-quality scans now catch dead citation markers/truncation fragments. Verification: `python -m pytest -q` 195 passed, `python -m stock_research validate --today 2026-05-13` OK, `python -m stock_research memory validate` OK.
- Main SDK issue resolved after OpenAI API credit was added and validation gates were tightened. Final AMZN/AAPL full run completed with providers_execute, analysis_execute, main SDK orchestration, zero SDK quality findings, and `agents/runs/2026-05-16_weekly/orchestration_report.md` status `complete`.
- Quality-gate lesson from AMZN run: proposal `source_ids` may be real repo artifact paths when they exist; direct trade wording checks must not flag ordinary business phrases like `Sell on Amazon`.
- Fanout task names are generated as `{lane}_{ticker.lower()}` from the requested ticker. They are run labels, not ticker-specific agent code.
- Manual market-research command: `python -m stock_research market-research run --topic "robotics suppliers in Europe" --subject-type industry --write --execute-providers`.
- Manual market-research live SDK command: `python -m stock_research market-research run --topic "robotics suppliers in Europe" --subject-type industry --write --execute-providers --execute-orchestrator`.
- Candidate-review bridge command: `python -m stock_research market-research candidate-review --run-id RUN_ID --write --queue-review`.
- Candidate-followup bridge command: `python -m stock_research market-research candidate-followup --run-id RUN_ID --review-id HRQ-0004 --write`.
- Candidate verification result command: `python -m stock_research market-research candidate-verification-result --run-id RUN_ID --review-id HRQ-0004 --write`.
- Candidate promotion command: `python -m stock_research market-research candidate-promote --run-id RUN_ID --review-id HRQ-0004 --write`.
- Human-review digest command: `python -m stock_research human-review digest --write`.
- Human-review decision command: `python -m stock_research human-review decide --set HRQ-0004=approved --note "Run verification." --write`.
- Portfolio review dry-run command: `python -m stock_research agent-runtime run --run-id RUN_ID --agent-id portfolio_review_orchestrator --task "portfolio review sub-orchestrator"`.
- Memory evaluation dry-run command: `python -m stock_research agent-runtime run --run-id RUN_ID --agent-id memory_evaluation_orchestrator --task "memory evaluation sub-orchestrator"`.
- Current digest artifact: `agents/human_review_digest.md`.
- Manual discovery gates: no Grok-only monitoring promotion, source ids required, verification status required, active rejected cooldown blocks promotion, rumor-flagged leads stay verification-limited.
- SDK evidence tool: `load_evidence_packet` lets specialists load summarized provider-neutral JSON packets by id/path. Use it for market-research specialists; do not rely on markdown-only evidence artifacts.
- Live validation artifacts:
  - `agents/runs/2026-05-10_manual-market/market_research/robotics_suppliers_in_europe_manual_market_research.md`
  - `agents/runs/2026-05-10_manual-market-energy-storage/market_research/grid_scale_energy_storage_manual_market_research.md`
  - `agents/runs/2026-05-10_manual-market-energy-storage/market_research/grid_scale_energy_storage_market_research.md`
- Dependency install command used: `python -m pip install -e .`.
- Install warning observed: `openai-agents` pulled `starlette 1.0.0`, which conflicts with an unrelated installed `fastapi 0.117.1` requirement in this environment. The repo does not currently use FastAPI, but revisit this if a FastAPI service is added later.
- 2026-05-16 company-file/hygiene slice:
  - Implemented scoped factual company-file updater: `python -m stock_research company-file apply-factual-updates --run-id RUN_ID --write`.
  - Weekly runner now auto-applies this low-risk factual sync only after executed analysis when opportunity-assessment artifacts exist.
  - AMZN factual update was refreshed after formatter QA exposed raw dict rendering; formatter now extracts `claim`/`summary` text and formats percent fields.
  - FYI summary artifact: `agents/runs/2026-05-16_weekly/company_file_factual_updates.md`.
  - Implemented artifact inventory/index command: `python -m stock_research artifact-hygiene inventory --write`; output `archive/research_index.md`.
  - Validation: `python -m pytest -q` passed with 207 tests.
  - Remaining: archive/move command, run-finalization archive proposals, broader thesis/status company-file proposal UX tests, notification/scheduling.
- 2026-05-16 readiness hardening slice:
  - Implemented archive move command: `python -m stock_research artifact-hygiene archive [--write]`.
  - Archive moves are dry-run by default and only move `archive_candidate` markdown artifacts into `archive/runs/{year}/{run_id}/...`; active ticker artifacts and open HRQ context stay in place.
  - Run finalization now writes `agents/runs/{run_id}/archive_proposals.md`; 2026-05-16 weekly currently has 0 archive candidates at the 30-day threshold.
  - Implemented run-end human-review summary: `agents/runs/{run_id}/human_review_digest_summary.md` for manual market runs, candidate review, and SDK `agent-runtime run --write`.
  - Implemented category state updater: `python -m stock_research category-state update --run-id RUN_ID --write`; weekly runs now call it.
  - Applied category state update to current repo for `2026-05-16_weekly`.
  - Added thesis/status proposal UX test and human-facing report-quality golden tests.
  - Validation: focused readiness tests passed; full `python -m pytest -q` passed with 213 tests.
  - Remaining before remote/set-and-forget use: notification/email digest automation, model optimization, scheduled market-research fanout after manual loop remains stable, and ongoing report-quality iteration from new real outputs.
- 2026-05-15 model-routing slice:
  - Implemented `agents/model_routing.yaml` plus `stock_research/model_routing.py`.
  - Strong/balanced/fast OpenAI API routes default to `gpt-5.5` for now; xAI X-search routes default to `grok-4.3`.
  - Codex app/automation remains the preferred manual-mode runner for command execution, report review, prompt iteration, synthesis critique, and file edits because it can use the user's Codex GPT-5.5 high environment. Repo Python cannot directly call the current Codex chat model internally.
  - Wired routing into SDK `RunConfig.model`, memory writer, weekly/manifest xAI tasks, manual market research, candidate follow-up, provider runner, and CLI xAI search.
  - Inspection command: `python -m stock_research model-routing show --route main_orchestrator`.
  - Validation so far: `tests/test_model_routing.py` passed and route inspection commands returned expected GPT-5.5/fast/Grok routes.
- 2026-05-15 Codex automation/rules slice:
  - Codex app automation `biweekly-holdings-and-monitoring-research` is active for tracked holdings/monitoring research every two weeks on Saturday at 08:00, starting 2026-05-16.
  - Automation command is intentionally exact: `C:\Python313\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis --execute-orchestrator --orchestrator-timeout-seconds 900`.
  - Updated `C:\Users\valen\.codex\rules\default.rules` with narrow `prefix_rule` entries for the exact command and the equivalent PowerShell wrapper.
  - Validated with `codex execpolicy check`: exact direct command and PowerShell wrapper return `decision: allow`; `git fetch` and arbitrary `stock_research provider-tasks --execute` remain unallowlisted.
  - Dry-run with `C:\Python313\python.exe -m stock_research run-weekly` succeeds from repo root, confirming editable install/Python entrypoint works.
- 2026-05-15 holdings update:
  - Replaced the old AMZN validation holding with the user's current holding list: AXTI, NBIS, MU, GOOGL, IREN, OSS, TE, AMBA, AVAV, KRKNF.
  - Removed the AAPL monitoring validation seed so `Run now` focuses on real holdings only.
  - Created current-holding company stub files for all 10 tickers.
  - Ticker assumptions to verify with user later if needed: `Ambarelly` -> AMBA / Ambarella Inc.; `Iren` -> NASDAQ IREN Limited; Kraken Robotics -> OTCQB KRKNF for US ticker compatibility, with primary Canadian listing TSX-V PNG.
  - Dry-run validation: repo has 10 current holdings, 0 monitoring rows, `run-weekly` plans 81 provider tasks and 50 analysis tasks for run id `2026-05-16_weekly`.
- 2026-05-15 model-cost/legacy-model check:
  - Active repo routes resolve OpenAI API calls to `gpt-5.5` and xAI calls to `grok-4.3`; no active source, `.env`, or current process env references `gpt-4.1`.
  - Added router guard so `gpt-4.1` / `gpt-4.1-2025-04-14` overrides raise instead of silently running.
  - Official OpenAI docs checked: `gpt-5.5` exists; no official `gpt-5.5-mini` route was found. Cheaper route candidates are `gpt-5.4-mini` or `gpt-5-mini` if we deliberately trade cost vs quality later.
  - Current 10-holding dry run plans 81 provider tasks: 22 Exa, 11 xAI/Grok, 10 yfinance, 10 FMP, 10 Alpha Vantage, 9 Polygon/Massive, 9 SEC; and 50 analysis tasks.
- 2026-05-15 model-cost optimization:
  - User clarified that routine API synthesis should not use `gpt-5.5` everywhere and that there is no `gpt-5.5-mini`.
  - Updated defaults: strong routes stay on `gpt-5.5`; balanced/fast/nano routes now use `gpt-5.4-mini`.
  - Internal `fast` tier is just a repo route name, not OpenAI priority processing. We use standard processing unless explicitly changing API processing mode later.
- 2026-05-16 Codex-supervised workflow implementation:
  - Added `stock_research/codex_review_pack.py` and wired weekly runs to write `codex_supervised_review_pack.md/json`.
  - Default scheduled automation now omits `--execute-orchestrator`; Codex app automation is the outer synthesis layer and should write `codex_supervised_review.md`.
  - Updated `C:\Users\valen\.codex\automations\biweekly-holdings-and-monitoring-research\automation.toml` to run the exact lower-cost command and to instruct Codex to read the review pack, inspect final digest/opportunity reports/quality/memory/hygiene/HRQ, and fix poor outputs before finalizing.
  - Updated `C:\Users\valen\.codex\rules\default.rules` with narrow allow rules for the lower-cost command. The old API SDK command remains only as an explicit benchmark/remote-mode allowance.
  - Durable decision: Codex-supervised mode should preserve the same learning loop as API mode: run summary, quality report, memory reflection/drafts/review, finalization, category state updates, artifact hygiene, company-file factual sync, and human-review digest.
- 2026-05-16 first biweekly Codex-supervised automation run:
  - `C:\Python313\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis` wrote the review pack, final digest, 10 opportunity reports, 10 company-news reports, 10 financial reports, memory/finalization artifacts, category state updates, and company-file factual updates.
  - Initial blocker: `C:\Python313` did not have `openai-agents`; non-SDK CLI paths still imported SDK registry code. Fixed with lazy SDK imports in `scheduled_runner.py` and `agent_runtime/__init__.py`.
  - Follow-up hardening: `agent_runtime/runner.py`, `agent_runtime/tracing.py`, and injected-executor scheduled-run paths also need to import cleanly without `openai-agents`; focused unittest coverage now passes under `C:\Python313`.
  - Run status remains `needs_review` because nine FMP provider packets were missing and most financial reviews need human review; this is a coverage/provider issue, not a Codex-supervised synthesis failure.
  - Report QA found leaked Grok `[[n]]` citation markers in opportunity/company-file prose. Patched opportunity and factual-update formatters, regenerated affected opportunity reports/final digest, refreshed factual company-file rows, and verified no `[[n]]` markers remain in human-facing outputs.
  - Current attention ranking from digest: MU and GOOGL are strongest `constructive_but_watch`; KRKNF is also constructive but blocked for missing forward valuation/target context; AMBA is weakest/riskier; all high-risk names need financial review gates resolved before thesis changes.
- 2026-05-16 automation postmortem hardening:
  - Root causes were mixed: Codex-supervised path exposed lazy SDK import gaps and stale generated-directory cleanup; the new 10-stock holding list exposed provider tier/rate-limit gaps and weaker coverage for smaller/OTC names.
  - FMP HTTP 402 premium/tier responses and Alpha Vantage rate-limit responses now write explicit unavailable evidence packets instead of missing-provider quality failures.
  - `scheduled_runner` cleanup now removes stale `portfolio_review` and `memory_evaluation` directories from old API-mode runs so they cannot contaminate Codex-supervised outputs.
  - Human report formatter/validator now rejects mojibake, dead citation fragments, visible truncation, and dangling excerpt tails such as `(up.`, `implying.`, `hig.`, or `while.`.
  - Rebuilt `2026-05-16_weekly` from existing evidence after patches: 131 evidence packets, 0 provider errors, 0 deterministic quality findings, 10 opportunity reports, 10 company-news reports, 10 financial reports, final digest, HRQ digest, company-file factual summary, and Codex review pack.
  - Current run still has `needs_review`, which is expected because several financial reviews have material conflicts/low-confidence metrics. This is a human/financial-review gate, not a provider execution failure.
- 2026-05-16 provider fallback key slice:
  - Added optional fallback keys `FMP_API_KEY2` and `ALPHA_VANTAGE_API_KEY2`.
  - Provider execution now tries the primary key first, retries the secondary key only on tier/subscription, rate-limit/quota, or credential-style unavailable errors, and writes sanitized attempt labels only.
  - If both keys fail, the workflow still writes explicit unavailable evidence packets so the automation can continue with the rest of the data sources.
- 2026-05-16 biweekly Codex-supervised run at 14:21 Europe/Berlin:
  - Ran the exact lower-cost automation command: `C:\Python313\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis`.
  - The command returned nonzero because status was `needs_review`, but the workflow wrote the expected run artifacts for `2026-05-16_weekly`: 131 evidence packets, 0 deterministic quality findings, 10 opportunity assessments, final digest, HRQ digest, company-file factual sync, memory/finalization artifacts, archive proposals, and review pack.
  - Wrote `agents/runs/2026-05-16_weekly/codex_supervised_review.md` as the final Codex synthesis.
  - Main attention ranking: MU and AVAV strongest; IREN/NBIS are interesting but capex/debt execution-sensitive; AMBA/AXTI/KRKNF are constructive but need catalyst verification; GOOGL/OSS/TE need financial-review gates resolved before thesis updates.
  - Open review surface remains `agents/human_review_digest.md` with 20 open items, including AMKR HRQ-0053 and older verification-only candidate baskets.
  - Validation passed: human-facing markdown check for the Codex review, `memory validate`, and repo `validate --today 2026-05-16`.
  - No durable operational memory update was needed; existing Codex-supervised/report-quality/provider-unavailable lessons cover the observed behavior.
  - Follow-up implementation gap: reduce noisy peer extraction and distinguish metadata-only financial conflicts from thesis-relevant conflicts so routine runs do not stay `needs_review` for harmless exchange/name normalization.
- 2026-05-16 manual review of latest automation result:
  - Confirmed the latest run is operationally good, not blocked: provider tasks 81/81 executed, analysis tasks 50/50 executed, quality findings 0, finalization complete, memory reflection issues 0, and human-facing report-quality checks passed.
  - `needs_review` currently means human/analyst review gates are open, not that the automation crashed. Main gates are GOOGL company-name normalization, OSS/TE exchange-code normalization, KRKNF single-provider/OTC coverage, plus 20 open HRQ rows.
  - FMP/Alpha fallback logic was exercised: both keys were tried where primary failed, but provider plan limits still returned unavailable packets for most FMP names and all Alpha names. This is a coverage limitation, not a missing fallback implementation.
- 2026-05-16 automation stabilization follow-up:
  - Official provider docs were rechecked. FMP stable endpoints are `quote`, `profile`, `key-metrics-ttm`, and `ratios-ttm` with `symbol`; Alpha uses `GLOBAL_QUOTE` and `OVERVIEW` with `function`, `symbol`, and `apikey`.
  - Live key smoke: FMP primary/secondary both work for AAPL/GOOGL. For AXTI/KRKNF, FMP blocks quote/TTM endpoints with 402 plan/ticker coverage but returns profile data. Alpha primary/secondary both returned Alpha standard daily/rate-limit messages, so params are correct but quota/plan is limiting.
  - Implemented FMP partial endpoint preservation: usable profile data is kept as medium-confidence FMP evidence with endpoint-level unknowns, and blocked endpoints retry the secondary key before finalizing.
  - Implemented financial metadata normalization: company-name/share-class differences and exchange aliases (`XNAS`/`NCM`, `XNYS`/`NYQ`) are metadata/watch items, not thesis blockers.
  - Rebuilt downstream only from existing evidence: financial_compare, financial_review, opportunity_assessment, run_summary, quality_report, finalization, factual company-file sync, final_digest, HRQ digest, and Codex review pack. No broad provider rerun was needed.
  - Current fixed run state: final digest `ready`, review pack `ready`, quality findings 0, scheduled status should be `complete` when no execution errors occur. KRKNF remains legitimately `partial_review` due OTC/single-provider coverage.
  - Remaining: smaller/OTC names still need better forward valuation/analyst-target coverage and cleaner peer/excerpt synthesis.
