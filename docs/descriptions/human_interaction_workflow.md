# Human Interaction Workflow

Last updated: 2026-05-15

## Goal

Make Codex chat the primary human interface for this stock research repo. The user should be able to give natural-language input, and Codex should translate it into durable repo state that the automated weekly workflow can use.

Manual file edits are allowed, but the normal path should be chat first.

For the concise human-facing usage guide, start with `docs/HUMAN_USAGE_GUIDE.md`.

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

## Current Implementation

The deterministic Python core can classify and queue human requests:

```powershell
python -m stock_research classify-request "Research ASML, TSM, AMD, and SAP"
python -m stock_research add-request "Look into European grid infrastructure suppliers" --priority high
python -m stock_research route-request "Research ASML, TSM, AMD, and SAP" --priority high
```

The current classifier and router are keyword-based and deterministic. They are useful for intake plumbing, but they are not a replacement for a future specialist triage agent.

Current routing behavior:

- stock research: adds monitoring CSV rows and creates company stub files,
- industry research: creates an industry research file and adds a research priority,
- theme tracking: creates a theme research file and adds a research priority,
- strategy change: appends a strategy input and creates a human review item,
- alert review: records the request only,
- manual run: creates a manual run manifest,
- stock status move: creates a human review item instead of moving the stock automatically.

Human review details are defined in `docs/descriptions/human_review_operating_model.md`.

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

Review surface: `agents/human_review_digest.md`

Use `python -m stock_research human-review digest --write` after manual or weekly runs to summarize open review items by decision type and priority. The digest is the preferred user-facing view; the queue remains the durable source of truth. The digest should always state the allowed human decisions concisely: approve, reject, mark needs more research, or leave open.

The user should normally review the digest first, not every sub-report. Deeper reports such as `portfolio_review.md`, `candidate_review.md`, `candidate_verification_result.md`, `orchestrator_update_proposals.md`, and `memory_evaluation.md` are context links for Codex, the orchestrator, and human drill-down.

`portfolio_review_orchestrator` is a synthesis layer for holdings/monitoring/rejected state and open decisions. Its report is read by the main orchestrator and by Codex when preparing a summary. The human reads it only when the digest points to a portfolio-level decision or the user asks for deeper context.

Decision writer: `python -m stock_research human-review decide --set HRQ-0004=approved --note "Run verification." --write`

Use the decision writer after the user tells Codex which HRQ ids to approve, reject, leave open, supersede, or mark as needing more research. This command only updates `agents/human_review_queue.md` and refreshes `agents/human_review_digest.md`; separate approval-gated commands still perform follow-up verification, company-file updates, stock moves, or monitoring promotion.

Asynchronous rule: a run should not stop all work because one branch needs user review. It should write the HRQ row, refresh the digest, continue independent safe work, and mark only the gated branch as waiting for human input.

Notification rule: for now, Codex chat plus repo artifacts are the canonical approval path. Later notification automation may send the digest by app notification or email, but email should initially be notification-only. Do not treat an email as an approval source unless a strict future email-ingestion workflow is implemented and tested.

For discovery candidates, the normal approved path is:

```powershell
python -m stock_research market-research candidate-followup --run-id RUN_ID --review-id HRQ-0004 --write
python -m stock_research provider-tasks --manifest agents\runs\RUN_ID\market_research\candidate_verification_manifest.json --execute
python -m stock_research analysis-tasks --manifest agents\runs\RUN_ID\market_research\candidate_verification_manifest.json --execute
python -m stock_research market-research candidate-verification-result --run-id RUN_ID --review-id HRQ-0004 --write
```

Verification results are written to `agents/runs/{run_id}/market_research/candidate_verification_result.md`. Promotion to monitoring is separate and remains blocked unless the HRQ row is approved, the candidate-review decision is `monitoring_candidate`, and required verification artifacts exist.

Company-file updates should not normally ask the user for approval when they are low-risk factual updates with source-backed evidence. The desired behavior is:

- auto-apply low-risk factual updates through a scoped writer,
- summarize file/section/source changes as FYI in the run-end digest,
- keep thesis changes, opinion changes, stock moves, strategy changes, and buy/sell/position-size decisions approval-gated.

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
- "Approve HRQ-0004 for verification and reject HRQ-0005."

Expected Codex actions:

- Read `agents/human_review_queue.md`.
- Read latest `agents/runs/*/run_summary.md` and category state files when available.
- Summarize decisions needed, supporting evidence, and suggested next action.
- If the user gives explicit HRQ decisions, update the queue with `human-review decide --write` and then run only the relevant approved follow-up command.

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
