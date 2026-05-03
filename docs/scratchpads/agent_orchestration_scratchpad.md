# Agent Orchestration Scratchpad

> Living memory for the stock research agent architecture.
> Keep entries short and scannable. Do not store secrets.

## Goal

- Build a Python stock tracking and investment research system with deterministic kickoff steps, specialist agents, orchestrator synthesis, repo-file updates, and continuous learning.

## Current Plan

- [x] Inspect current repo structure.
- [x] Research OpenAI Agents SDK and finance-agent patterns.
- [x] Draft initial architecture description.
- [x] Create long-running plan file.
- [x] Record first user validation answers.
- [x] Create explicit backlog file.
- [x] Decide first implementation slice.
- [x] Create repo templates and file conventions.
- [x] Add human-to-system intake layer planning files.
- [x] Add stdlib-only deterministic Python core and CLI.
- [x] Add deterministic human request router.
- [x] Add provider-neutral evidence packet schema and artifact writer.
- [x] Add SEC EDGAR provider integration.
- [x] Run live SEC EDGAR smoke test.
- [x] Add yfinance provider integration and live smoke test.
- [x] Add Exa search/contents provider integration and live smoke tests.
- [x] Wire default SEC/yfinance/Exa provider tasks into weekly manifest.
- [x] Add dry-run-by-default provider task runner.
- [x] Replace direct X.com API with xAI Grok x_search provider and manifest tasks.
- [x] Run live xAI Grok `x_search` smoke test.
- [ ] Validate updated architecture with user.

## Key Decisions and Why

- 2026-04-30: Proposed deterministic-first workflow because recurring stock tracking needs predictable coverage before open-ended agent judgment.
- 2026-04-30: Proposed separate writer specialists so research agents do not make broad, hard-to-review file edits.
- 2026-04-30: Proposed run artifacts plus agent memory so future runs can learn from bad sources, failed prompts, and repeated routing mistakes.
- 2026-04-30: Created initial architecture description and long-running implementation plan; pending user validation.
- 2026-04-30: User confirmed US and Europe scope, tracked-stock alerts plus new-stock discovery alerts, approved providers, Saturday weekly cadence, and 6-week rejected-stock cooldown.
- 2026-04-30: Added separate backlog file so future chats can find priority tasks quickly.
- 2026-04-30: First implementation slice is repo templates and file conventions before Python runtime code.
- 2026-04-30: Created CSV headers, category state files, company template, strategy starter files, and market research folder READMEs.
- 2026-05-03: Reviewed agent SDK options before runtime implementation; OpenAI Agents SDK remains plausible, but final choice should consider Pydantic AI, LangGraph, and Cursor SDK based on provider routing, durability, and repo-writing needs.
- 2026-05-03: User validated need for a formal human-to-system intake layer. Codex chat is planned as the main interface; proactive user requests go to `docs/plans/human_research_requests.md`, while system approval items go to `agents/human_review_queue.md`.
- 2026-05-03: Added `stock_research/` deterministic core before agent framework work. No external dependencies.
- 2026-05-03: Added deterministic request router. It routes clear requests into monitoring rows/company files, industry/theme research files, research priorities, human review items, or manual run manifests.
- 2026-05-03: Added provider-neutral evidence schema so SEC, Exa, xAI/Grok X sentiment, yfinance, FMP, Polygon, Alpha Vantage, macro, and future providers can emit the same packet format.
- 2026-05-03: Added SEC EDGAR provider. It needs no API key, but live requests require `SEC_USER_AGENT` or `--user-agent`.
- 2026-05-03: SEC live smoke test passed for AAPL. The provider now handles SEC gzip-compressed responses and writes validated raw/evidence artifacts.
- 2026-05-03: Exa should be exposed as deterministic provider tools first, then wrapped by specialist agents. This keeps provider behavior auditable and reusable by Codex, orchestrators, and specialists.
- 2026-05-03: yfinance and Exa provider tools were added. yfinance live AAPL smoke passed. Exa live search/contents smoke passed after adding explicit `User-Agent` and `Accept` headers.
- 2026-05-03: Future specialists should choose among Exa `general`, `news`, `industry`, `company`, and `contents` tools based on task. The deterministic weekly kickoff should also run Exa by default for tracked-stock news, strategy/research-priority industry/theme scans, candidate discovery, and human input queue items.
- 2026-05-03: Weekly manifests now contain concrete `provider_tasks`. The provider task runner is dry-run by default and only executes live provider calls when `--execute` is passed.
- 2026-05-03: User corrected provider intent: do not use direct X.com API. Use xAI/Grok via `XAI_API_KEY` with built-in `x_search` for X sentiment/latest-news research.
- 2026-05-03: Live xAI/Grok `x_search` smoke test passed for AMD and wrote validated raw/evidence artifacts.

## What We Learned

- Repo is currently scaffolding only: top-level folders exist, but no stock CSVs, company markdown files, agent code, README, or SETUP yet.
- `MEMORY.md` exists but has no active memory entries.
- `docs/descriptions/` and `docs/plans/` were empty before this architecture pass.
- Official OpenAI Agents SDK supports both code orchestration and LLM orchestration, plus agents as tools, handoffs, guardrails, sessions, and tracing.
- SEC EDGAR provides official JSON APIs for submissions and XBRL financial data without API keys.
- `README.md` and `SETUP.md` do not exist yet, so there was nothing to validate against after this docs-only pass.
- Additional useful source candidates: OpenBB, Twelve Data, EODHD, Finnhub, Nasdaq Data Link, FRED, ECB, Eurostat, Companies House, and future ESMA ESAP.
- Stock tracking CSV filenames are `current_holdings.csv`, `monitoring.csv`, and `rejected.csv`.
- Detailed company files live under `stock_tracking/stock_info_files/{current_holdings,monitoring,rejected}/`.
- Human interaction docs now exist: `docs/descriptions/human_interaction_workflow.md` and `docs/descriptions/repo_map.md`.
- Recurring user research priorities live in `strategy/research_priorities.md`.
- Human input and human review are intentionally separate queues.
- Deterministic CLI commands now exist: `summary`, `validate`, `stale`, `manifest`, `classify-request`, and `add-request`.
- `route-request` now appends to the human input queue and updates target artifacts where deterministic routing is safe.
- Evidence packets are JSON files under `agents/runs/{run_id}/evidence_packets/`.
- `python -m stock_research evidence new ...` and `evidence validate ...` are available.
- SEC command exists: `python -m stock_research sec company --ticker AAPL --run-id 2026-05-09_weekly`.
- SEC live smoke command succeeded after adding compressed-response decoding: `python -m stock_research sec company --ticker AAPL --run-id 2026-05-09_weekly`.
- Live SEC AAPL artifacts exist under `agents/runs/2026-05-09_weekly/raw/sec_edgar/` and `agents/runs/2026-05-09_weekly/evidence_packets/`.
- yfinance command exists: `python -m stock_research yfinance company --ticker AAPL --run-id 2026-05-09_weekly`.
- Exa commands exist: `python -m stock_research exa search ...` and `python -m stock_research exa contents ...`.
- Live yfinance AAPL and Exa smoke artifacts exist under `agents/runs/2026-05-09_weekly/`.
- Exa default weekly usage should be: holdings/monitoring -> `news`; industry/theme priorities -> `industry` or `general`; discovery -> `company`; high-value result follow-up -> `contents`.
- Manifest provider tasks now plan SEC/yfinance/Exa kickoff work before orchestrator synthesis.
- Provider task runner command exists: `python -m stock_research provider-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json`.
- xAI Grok command exists: `python -m stock_research xai x-search ...`.
- Manifest provider tasks now include Grok `x_search` sentiment/latest-news checks.
- Live xAI Grok AMD smoke packet exists: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_xai_grok_company_amd.json`.
- `python -m unittest discover -s tests` is the working test command in this repo.
- Cursor SDK is promising for coding-agent automation, but it is public beta and TypeScript-first; it looks better for repo maintenance agents than for the core stock-research runtime.
- OpenAI Agents SDK supports the repo's manager/specialist pattern, tracing, guardrails, Pydantic outputs, sessions, and non-OpenAI model routing via Any-LLM/LiteLLM, but provider capability gaps must be tested.
- Pydantic AI is a strong Python-native alternative for this repo because it is type-first, model-agnostic, OpenRouter-aware, and fits the planned evidence packet schemas.
- LangGraph is the strongest candidate if durable execution, resumable workflows, human approval checkpoints, and explicit graph state become the dominant requirements.

## Open Questions

- Initial stock universe and example companies?
- Priority European markets?
- Provider source-of-truth hierarchy?
- Confidence scoring format?
- What changes need human approval before file writes?
- Agent framework decision: OpenAI Agents SDK, Pydantic AI, LangGraph, or a hybrid?
- Exact implementation shape for Codex chat request classification and manual run triggering.

## Next Steps

- Review updated `docs/descriptions/investment_agent_workflow.md` and `docs/plans/investment_agent_backlog.md` with the user if needed.
- Next implementation work should add paid market-data cross-check providers such as FMP/Polygon/Alpha Vantage, create agent memory files, or build the first synthesis/writer specialist around evidence packets.
- Before Priority 4 agent implementation, run a thin spike comparing OpenAI Agents SDK vs Pydantic AI for one evidence-packet specialist and one orchestrator call.
- Consider LangGraph only if the first spike shows that explicit resumable graph state is needed earlier than planned.
- Add README and SETUP when runtime dependencies are introduced.

## Risks / Gotchas

- Social sentiment is noisy and should not be treated as fact.
- LLMs can overstate confidence if sources are weak or conflicting.
- File writers need tight target-file scopes to avoid broad repo churn.
- Buy/sell actions should remain human-approved.
- Data providers can disagree on metrics; preserve provider/source metadata.
- Do not choose Cursor SDK as the main research runtime unless its beta API proves strong for non-coding tool orchestration, source capture, and Python integration.
- Any multi-provider SDK path needs provider-specific tests for tool calling, structured outputs, usage/cost reporting, and streaming.
- SEC may return compressed responses even for JSON endpoints; keep compression decoding in provider fetch helpers.
- Exa requests can fail with HTTP 403 code 1010 if the default Python HTTP client headers are too sparse. Keep explicit `User-Agent` and `Accept: application/json` headers.
- yfinance is useful for quick snapshots but should be cross-checked before high-impact decisions.
- Grok/X evidence is social signal unless independently verified. Treat it as sentiment/community chatter, not standalone fact.
- Do not reintroduce direct X.com API bearer-token search unless the user explicitly asks for that reversal.

## Commands / Environment Notes

- `rg --files` failed with Access denied in this environment; PowerShell `Get-ChildItem` worked.
- Current repo path: `C:\Users\valen\Documents\Code\stocks`.
- SEC live smoke test output packet: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_sec_edgar_company_aapl.json`.
- yfinance live smoke packet: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_yfinance_company_aapl.json`.
- Exa live smoke packets: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_exa_industry_semiconductors.json`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_exa_theme_sec_edgar_docs.json`.
- xAI Grok live smoke packet: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_xai_grok_company_amd.json`.
- Current written weekly manifest with provider tasks: `agents/runs/2026-05-09_weekly/manifest.json`.
