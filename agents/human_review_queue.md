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
| HRQ-0004 | 2026-05-10 | Review Grok/X discovery lead FLNC (FLNC) for follow-up verification. | Approve Exa/filing/financial verification of this Grok-only lead, or ignore it. | medium | open | agents/runs/2026-05-10_manual-market-energy-storage/market_research | agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0001 | Candidate surfaced from grok with verification=grok_only, hype=high, cooldown=not_rejected. Tickers: FLNC. Source IDs: xai_x_source_1, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6, xai_x_source_7, xai_x_source_8. |
| HRQ-0005 | 2026-05-10 | Review Grok/X discovery lead NRGV (NRGV) for follow-up verification. | Approve Exa/filing/financial verification of this Grok-only lead, or ignore it. | medium | open | agents/runs/2026-05-10_manual-market-energy-storage/market_research | agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0002 | Candidate surfaced from grok with verification=grok_only, hype=high, cooldown=not_rejected. Tickers: NRGV. Source IDs: xai_x_source_1, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6, xai_x_source_7, xai_x_source_8. |
| HRQ-0006 | 2026-05-10 | Review Grok/X discovery lead NXXT (NXXT) for follow-up verification. | Approve Exa/filing/financial verification of this Grok-only lead, or ignore it. | medium | open | agents/runs/2026-05-10_manual-market-energy-storage/market_research | agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0003 | Candidate surfaced from grok with verification=grok_only, hype=high, cooldown=not_rejected. Tickers: NXXT. Source IDs: xai_x_source_1, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6, xai_x_source_7, xai_x_source_8. |
| HRQ-0007 | 2026-05-10 | Review discovery candidate ADS-TEC Energy (ADSE) for verification before monitoring. | Approve follow-up company and financial verification before considering monitoring. | medium | approved | agents/runs/2026-05-10_manual-market-energy-storage/market_research | agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0004 | Candidate surfaced from exa with verification=exa_only, hype=unknown, cooldown=not_rejected. Tickers: ADSE. Source IDs: exa_result_1. Decision update 2026-05-11 by user: approved. Approved by user request for workflow validation; run candidate verification only, no monitoring promotion. |
| HRQ-0008 | 2026-05-10 | Review discovery candidate Clearway Energy, Inc. (CWEN) for verification before monitoring. | Approve follow-up company and financial verification before considering monitoring. | medium | open | agents/runs/2026-05-10_manual-market-energy-storage/market_research | agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0005 | Candidate surfaced from exa with verification=exa_only, hype=unknown, cooldown=not_rejected. Tickers: CWEN. Source IDs: exa_result_4. |
| HRQ-0009 | 2026-05-10 | Review discovery candidate Invinity Energy Systems (IES.L) for verification before monitoring. | Approve follow-up company and financial verification before considering monitoring. | medium | open | agents/runs/2026-05-10_manual-market-energy-storage/market_research | agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0006 | Candidate surfaced from exa with verification=exa_only, hype=unknown, cooldown=not_rejected. Tickers: IES.L. Source IDs: exa_result_2. |
