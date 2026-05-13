# Human Review Digest

Generated: 2026-05-13
Status: needs_user_review
Open items summarized: 15

## Summary

- Company File Updates: 2
- Monitoring Candidate Reviews: 1
- Grok/X Candidate Verification: 5
- Candidate Verification: 6
- Strategy / Workflow: 1

## Decision Options

- approve: allow the next gated follow-up step described in the row
- reject: close or ignore the item
- needs_more_research: keep open and request more evidence
- leave open: make no change

Monitoring candidates are not automatically added to monitoring. Grok/X verification items are earlier-stage social leads and only approve deeper verification.

## Priority Counts

- medium: 15

## Company File Updates

Proposed edits to existing company files. Duplicate tickers can be valid when separate proposals touch different parts of the file.

| Priority | ID | Target | Verification | Suggested action | Why this is here / where to read | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| medium | HRQ-0002 | AAPL | not specified | Approve, reject, or request more research; approved proposals can then be applied. | This is a proposed company-file change; multiple rows for one ticker can be separate update proposals. Update AAPL company news: Q2 2026 record results, 17% revenue growth, Q3 guidance 14-17% growth, and CEO transition news as reported by reliable sources. | agents/runs/2026-05-09_weekly/orchestrator_update_proposals.md#ORP-0001 |
| medium | HRQ-0003 | AAPL | source validated | Approve, reject, or request more research; approved proposals can then be applied. | This is a proposed company-file change; multiple rows for one ticker can be separate update proposals. Update AAPL financial snapshot as-of 2026-05: price $284.2, market cap $4.157T, P/E 33.99, and other headline metrics from financial_compare, all source-validated and consistent. | agents/runs/2026-05-09_weekly/orchestrator_update_proposals.md#ORP-0002 |

## Monitoring Candidate Reviews

Source-backed discovery candidates that may be worth adding to monitoring after you review the linked evidence.

| Priority | ID | Target | Verification | Suggested action | Why this is here / where to read | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| medium | HRQ-0010 | AMKR | verified | Approve adding to monitoring, request more research, or reject/ignore. | Read the linked candidate group and market report first; approval means this source-backed lead may enter the monitoring approval path. Candidate surfaced from exa, grok with verification=verified, hype=unknown, cooldown=not_rejected. Tickers: AMKR. Source IDs: exa_result_1, xai_x_source_1, xai_x_source_10, xai_x_source_11, xai_x_source_12, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6, xai_x_source_7, xai_x_source_8, xai_x_source_9. | agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/candidate_review.md#CRG-0001 |

## Grok/X Candidate Verification

Early social/X leads from Grok. Approving these only starts verification; it does not add them to monitoring.

| Priority | ID | Target | Verification | Suggested action | Why this is here / where to read | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| medium | HRQ-0004 | FLNC | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | This is a social/X lead only; approval means run verification, not add to monitoring. Candidate surfaced from grok with verification=grok_only, hype=high, cooldown=not_rejected. Tickers: FLNC. Source IDs: xai_x_source_1, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6, xai_x_source_7, xai_x_source_8. | agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0001 |
| medium | HRQ-0005 | NRGV | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | This is a social/X lead only; approval means run verification, not add to monitoring. Candidate surfaced from grok with verification=grok_only, hype=high, cooldown=not_rejected. Tickers: NRGV. Source IDs: xai_x_source_1, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6, xai_x_source_7, xai_x_source_8. | agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0002 |
| medium | HRQ-0006 | NXXT | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | This is a social/X lead only; approval means run verification, not add to monitoring. Candidate surfaced from grok with verification=grok_only, hype=high, cooldown=not_rejected. Tickers: NXXT. Source IDs: xai_x_source_1, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6, xai_x_source_7, xai_x_source_8. | agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0003 |
| medium | HRQ-0043 | ASX, INTC, LPK, RMBS | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | This is a social/X lead only; approval means run verification, not add to monitoring. Candidate surfaced from grok with verification=grok_only, hype=unknown, cooldown=not_rejected. Basket contains 4 tickers across 4 lead(s). Tickers: ASX, INTC, LPK, RMBS. Source IDs: xai_x_source_1, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6. | agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/candidate_review.md#CRG-0002 |
| medium | HRQ-0044 | GLW, KLAC, LRCX, ONTO, TSM | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | This is a social/X lead only; approval means run verification, not add to monitoring. Candidate surfaced from grok with verification=grok_only, hype=unknown, cooldown=not_rejected. Basket contains 5 tickers across 5 lead(s). Tickers: GLW, KLAC, LRCX, ONTO, TSM. Source IDs: xai_x_source_1, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6. | agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/candidate_review.md#CRG-0003 |

## Candidate Verification

Leads that need more company/news/financial verification before any monitoring decision.

| Priority | ID | Target | Verification | Suggested action | Why this is here / where to read | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| medium | HRQ-0008 | CWEN | exa only | Approve follow-up verification or reject/ignore before any monitoring decision. | This lead needs company/news/financial verification before any monitoring decision. Candidate surfaced from exa with verification=exa_only, hype=unknown, cooldown=not_rejected. Tickers: CWEN. Source IDs: exa_result_4. | agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0005 |
| medium | HRQ-0009 | IES.L | exa only | Approve follow-up verification or reject/ignore before any monitoring decision. | This lead needs company/news/financial verification before any monitoring decision. Candidate surfaced from exa with verification=exa_only, hype=unknown, cooldown=not_rejected. Tickers: IES.L. Source IDs: exa_result_2. | agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0006 |
| medium | HRQ-0039 | WAF.DE | exa only | Approve follow-up verification or reject/ignore before any monitoring decision. | This lead needs company/news/financial verification before any monitoring decision. Candidate surfaced from exa with verification=exa_only, hype=high, cooldown=not_rejected. Tickers: WAF.DE. Source IDs: exa_result_3. | agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/candidate_review.md#CRG-0004 |
| medium | HRQ-0040 | SOI.PA | exa only | Approve follow-up verification or reject/ignore before any monitoring decision. | This lead needs company/news/financial verification before any monitoring decision. Candidate surfaced from exa with verification=exa_only, hype=unknown, cooldown=not_rejected. Tickers: SOI.PA. Source IDs: exa_result_2. | agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/candidate_review.md#CRG-0005 |
| medium | HRQ-0041 | SMHN.F | exa only | Approve follow-up verification or reject/ignore before any monitoring decision. | This lead needs company/news/financial verification before any monitoring decision. Candidate surfaced from exa with verification=exa_only, hype=unknown, cooldown=not_rejected. Tickers: SMHN.F. Source IDs: exa_result_5. | agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/candidate_review.md#CRG-0006 |
| medium | HRQ-0042 | XFAB.PA | exa only | Approve follow-up verification or reject/ignore before any monitoring decision. | This lead needs company/news/financial verification before any monitoring decision. Candidate surfaced from exa with verification=exa_only, hype=unknown, cooldown=not_rejected. Tickers: XFAB.PA. Source IDs: exa_result_4. | agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/candidate_review.md#CRG-0007 |

## Strategy / Workflow

Strategy or process changes that affect future runs.

| Priority | ID | Target | Verification | Suggested action | Why this is here / where to read | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| medium | HRQ-0001 | human-to-system intake | not specified | Approve, reject, or refine the workflow/strategy change. | This changes strategy or process; approve only if the workflow should remember it. Added from user request. | not linked |

## Suggested Codex Prompt

Tell Codex which HRQ ids to approve, reject, leave open, or mark as needing more research. Example:

`Approve HRQ-XXXX and HRQ-YYYY for follow-up verification; reject HRQ-ZZZZ; leave the rest open.`

Codex should record explicit decisions with `python -m stock_research human-review decide --set HRQ-XXXX=approved --write` before running any approved follow-up command.
