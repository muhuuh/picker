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
- Start deterministic core with human input queue/research priorities loading included from the beginning.
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

## Commands / Environment Notes

- `rg --files` failed with Access denied in this environment; PowerShell `Get-ChildItem` worked.
- Current repo path: `C:\Users\valen\Documents\Code\stocks`.
