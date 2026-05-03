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
