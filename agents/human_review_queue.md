# Human Review Queue

Last updated: 2026-05-03

## Purpose

This queue contains system-generated decisions or recommendations that require user approval.

This is separate from `docs/plans/human_research_requests.md`, which captures proactive user input.

## Requires Human Approval

- Buy, sell, or position-size recommendations.
- Moving a stock between current holdings, monitoring, and rejected.
- Overriding the 6-week rejected-stock cooldown.
- Major strategy changes.
- Treating a discovery candidate as high priority when evidence is incomplete.
- Any decision where sources conflict materially.

## Status Values

- `open`
- `approved`
- `rejected`
- `needs_more_research`
- `superseded`

## Review Items

| ID | Date Added | Item | Decision Needed | Priority | Status | Related Files | Evidence / Run Link | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HRQ-0001 | 2026-05-03 | Confirm human-to-system intake layer as part of the planned workflow. | Approve this planning addition before implementation logic depends on it. | medium | open | `docs/descriptions/human_interaction_workflow.md`, `docs/plans/human_research_requests.md`, `strategy/research_priorities.md` |  | Added from user request. |
| HRQ-0002 | 2026-05-07 | Review SDK file update proposal ORP-0001 for stock_tracking/stock_info_files/monitoring/AAPL.md. | Approve, reject, or request more research before any company-file writer applies this update. | medium | open | stock_tracking/stock_info_files/monitoring/AAPL.md | agents/runs/2026-05-09_weekly/orchestrator_update_proposals.md#ORP-0001 | Update AAPL company news: Q2 2026 record results, 17% revenue growth, Q3 guidance 14-17% growth, and CEO transition news as reported by reliable sources. |
| HRQ-0003 | 2026-05-07 | Review SDK file update proposal ORP-0002 for stock_tracking/stock_info_files/monitoring/AAPL.md. | Approve, reject, or request more research before any company-file writer applies this update. | medium | open | stock_tracking/stock_info_files/monitoring/AAPL.md | agents/runs/2026-05-09_weekly/orchestrator_update_proposals.md#ORP-0002 | Update AAPL financial snapshot as-of 2026-05: price $284.2, market cap $4.157T, P/E 33.99, and other headline metrics from financial_compare, all source-validated and consistent. |
