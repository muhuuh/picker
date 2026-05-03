# Human Interaction Workflow

Last updated: 2026-05-03

## Goal

Make Codex chat the primary human interface for this stock research repo. The user should be able to give natural-language input, and Codex should translate it into durable repo state that the automated weekly workflow can use.

Manual file edits are allowed, but the normal path should be chat first.

## Core Model

1. User tells Codex something in natural language.
2. Codex reads repo context:
   - `MEMORY.md`
   - `docs/descriptions/repo_map.md`
   - `docs/descriptions/investment_agent_workflow.md`
   - relevant scratchpads in `docs/scratchpads/`
   - `docs/plans/investment_agent_backlog.md`
   - `docs/plans/human_research_requests.md`
   - `strategy/`
   - `stock_tracking/`
   - relevant `market_research/` files
3. Codex classifies the request.
4. Codex updates the correct durable artifact.
5. Codex records or updates the request in `docs/plans/human_research_requests.md`.
6. Codex either:
   - marks the item for the next Saturday workflow,
   - performs immediate manual research if asked,
   - or asks for clarification when the request cannot be safely routed.

## Two Separate Queues

### Human Input Queue

Location: `docs/plans/human_research_requests.md`

Purpose: things the user wants the system to consider.

Examples:

- "Look into robotics suppliers in Europe."
- "I think battery recycling will matter next year."
- "Research these four stocks."
- "Add this industry to recurring market research."

### Human Review Queue

Location: `agents/human_review_queue.md`

Purpose: decisions or recommendations the system wants the user to approve.

Examples:

- Move a stock from monitoring to current holdings.
- Move a stock to rejected.
- Override a rejected-stock cooldown.
- Change strategy rules.
- Treat a discovery candidate as high priority.
- Consider buy, sell, or position-size actions.

## Request Types

### Stock Research Request

User examples:

- "Research ASML, TSM, AMD, and SAP."
- "Please check whether Novo Nordisk is still interesting."

Expected Codex actions:

- Add or update request in `docs/plans/human_research_requests.md`.
- If the stock should be tracked, add it to `stock_tracking/monitoring/monitoring.csv`.
- Create a company file from `docs/templates/company_stock_info_template.md` if needed.
- Link the company file from the CSV row.
- Mark whether research should happen immediately or in the next Saturday run.

### Industry Research Request

User examples:

- "I heard something about grid infrastructure, find interesting stocks."
- "Look into European defense suppliers."

Expected Codex actions:

- Add or update request in `docs/plans/human_research_requests.md`.
- Create or update a file in `market_research/industries/`.
- Add the industry to `strategy/research_priorities.md` if it should recur.
- Flag discovery agents to search for candidate stocks in the next run.

### Theme / Technology Tracking Request

User examples:

- "I think humanoid robotics will be critical next year."
- "Include nuclear power and SMRs in market research from now on."

Expected Codex actions:

- Add or update request in `docs/plans/human_research_requests.md`.
- Create or update a file in `market_research/themes/`.
- Update `strategy/research_priorities.md`.
- Update `strategy/investment_strategy.md` or `strategy/screening_criteria.md` if the theme changes the strategy.
- Mark the theme as recurring, one-time, or watch-only.

### Strategy Change Request

User examples:

- "From now on, avoid companies with heavy dilution."
- "Give more weight to profitable European industrial software companies."

Expected Codex actions:

- Update `strategy/investment_strategy.md`, `strategy/screening_criteria.md`, or `strategy/risk_rules.md`.
- Record durable/high-impact changes in `MEMORY.md` when appropriate.
- Add a human review queue item if the change is major or ambiguous.

### Alert Review Request

User examples:

- "Show me what needs my decision this week."
- "What changed for our current holdings?"

Expected Codex actions:

- Read `agents/human_review_queue.md`.
- Read latest `agents/runs/*/run_summary.md` and category state files when available.
- Summarize decisions needed, supporting evidence, and suggested next action.

### Manual Run Request

User examples:

- "Run research now for these stocks."
- "Do an immediate industry scan for grid infrastructure."

Expected Codex actions:

- Record the request.
- Build a one-off run manifest when deterministic core exists.
- Run available deterministic tools and specialists when implemented.
- Save outputs under `agents/runs/YYYY-MM-DD_manual-*`.

### Stock Status Move Request

User examples:

- "Move this stock to rejected."
- "Start monitoring this company."

Expected Codex actions:

- Update the relevant CSV and company file.
- Update category state files.
- Add a human review item if the move has investment impact or overrides cooldown rules.

## Request Fields

Each human input queue item should track:

- ID
- date added
- request text
- request type
- priority
- status
- target tickers
- target industries/themes
- target files
- next run inclusion
- immediate action requested
- owner/agent
- result link
- notes

## Status Values

- `new`
- `triaged`
- `queued_for_weekly_run`
- `in_progress`
- `waiting_for_user`
- `done`
- `rejected`
- `superseded`

## Priority Values

- `low`
- `medium`
- `high`
- `urgent`

## Routing Rules

- Company-specific requests go to `stock_tracking/monitoring/` unless the user explicitly says current holding or rejected.
- Industry requests go to `market_research/industries/`.
- Technology/theme requests go to `market_research/themes/`.
- Recurring research priorities go to `strategy/research_priorities.md`.
- Strategy rules go to `strategy/investment_strategy.md`, `strategy/screening_criteria.md`, or `strategy/risk_rules.md`.
- Approval needs go to `agents/human_review_queue.md`.
- Major durable decisions also go to `MEMORY.md`.

## Guardrails

- Do not assume a user mention means buy, sell, or position size.
- Do not add a stock to current holdings unless the user explicitly confirms it is held.
- Do not override rejected-stock cooldown unless the user explicitly requests it.
- Keep human input items separate from system approval items.
- Keep every material research claim tied to a source or run artifact.
