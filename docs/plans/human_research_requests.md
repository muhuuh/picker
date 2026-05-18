# Human Research Requests

Last updated: 2026-05-18

## Purpose

This is the human input queue. It captures proactive user requests so they are not lost between chats and so the automated Saturday workflow can pick them up.

This is separate from `agents/human_review_queue.md`, which is for system-generated items requiring user approval.

## How To Use

- Add one request per row in the table.
- Keep the original user wording in `Request`.
- Use `Next Run` to indicate whether the Saturday workflow should include it.
- Use `Result Link` to point to company files, market research files, or run artifacts after work is done.

## Request Types

- `stock_research`
- `industry_research`
- `theme_tracking`
- `strategy_change`
- `alert_review`
- `manual_run`
- `stock_status_move`
- `other`

## Status Values

- `new`
- `triaged`
- `queued_for_weekly_run`
- `in_progress`
- `waiting_for_user`
- `done`
- `rejected`
- `superseded`

## Requests

| ID | Date Added | Request | Type | Priority | Status | Tickers | Industries / Themes | Target Files | Next Run | Immediate Action | Owner / Agent | Result Link | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HIR-0001 | 2026-05-03 | Formalize the human-to-system intake layer for Codex chat and future automation. | strategy_change | high | done |  | human interaction workflow | `docs/descriptions/human_interaction_workflow.md`, `docs/descriptions/repo_map.md`, `strategy/research_priorities.md`, `agents/human_review_queue.md` | no | yes | Codex | `docs/descriptions/human_interaction_workflow.md` | Initial intake system design. |
| HIR-0002 | 2026-05-18 | Add LPKF Laser & Electronics SE and Sivers Semiconductors AB to holdings, research only these two like an automation run, and remove Kraken Robotics after sale. | manual_run | high | done | LPK.DE, SIVE.ST, KRKNF | advanced packaging, photonics, semiconductors, subsea robotics | `stock_tracking/current_holdings/current_holdings.csv`, `stock_tracking/rejected/rejected.csv`, `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/codex_supervised_review.md` | no | yes | Codex | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/codex_supervised_review.md` | Focused run completed for LPK.DE and SIVE.ST only; KRKNF moved to rejected after user-confirmed sale. |
