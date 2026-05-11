# Human Review Digest

Generated: 2026-05-11
Status: needs_user_review
Open items summarized: 8

## Summary

- Company File Updates: 2
- Grok/X Candidate Verification: 3
- Candidate Verification: 2
- Strategy / Workflow: 1

## Decision Options

- approve: allow the next gated follow-up step
- reject: close or ignore the item
- needs_more_research: keep open and request more evidence
- leave open: make no change

## Priority Counts

- medium: 8

## Company File Updates

| Priority | ID | Target | Verification | Suggested action | Evidence |
| --- | --- | --- | --- | --- | --- |
| medium | HRQ-0002 | AAPL | not specified | Approve, reject, or request more research; approved proposals can then be applied. | agents/runs/2026-05-09_weekly/orchestrator_update_proposals.md#ORP-0001 |
| medium | HRQ-0003 | AAPL | source validated | Approve, reject, or request more research; approved proposals can then be applied. | agents/runs/2026-05-09_weekly/orchestrator_update_proposals.md#ORP-0002 |

## Grok/X Candidate Verification

| Priority | ID | Target | Verification | Suggested action | Evidence |
| --- | --- | --- | --- | --- | --- |
| medium | HRQ-0004 | FLNC | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0001 |
| medium | HRQ-0005 | NRGV | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0002 |
| medium | HRQ-0006 | NXXT | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0003 |

## Candidate Verification

| Priority | ID | Target | Verification | Suggested action | Evidence |
| --- | --- | --- | --- | --- | --- |
| medium | HRQ-0008 | CWEN | exa only | Approve follow-up verification or reject/ignore before any monitoring decision. | agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0005 |
| medium | HRQ-0009 | IES.L | exa only | Approve follow-up verification or reject/ignore before any monitoring decision. | agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0006 |

## Strategy / Workflow

| Priority | ID | Target | Verification | Suggested action | Evidence |
| --- | --- | --- | --- | --- | --- |
| medium | HRQ-0001 | human-to-system intake | not specified | Approve, reject, or refine the workflow/strategy change. | not linked |

## Suggested Codex Prompt

Tell Codex which HRQ ids to approve, reject, leave open, or mark as needing more research. Example:

`Approve HRQ-XXXX and HRQ-YYYY for follow-up verification; reject HRQ-ZZZZ; leave the rest open.`

Codex should record explicit decisions with `python -m stock_research human-review decide --set HRQ-XXXX=approved --write` before running any approved follow-up command.
