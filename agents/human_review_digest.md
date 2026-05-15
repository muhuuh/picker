# Human Review Digest

Generated: 2026-05-15
Status: needs_user_review
Open items summarized: 20

## Summary

- Company File Updates / FYI: 2
- Monitoring Candidate Reviews: 1
- Grok/X Candidate Verification: 10
- Candidate Verification: 6
- Strategy / Workflow: 1

## Decision Options

- approve: allow the next gated follow-up step described in the row
- reject: close or ignore the item
- needs_more_research: keep open and request more evidence
- leave open: make no change

Monitoring candidates are not automatically added to monitoring. Grok/X and Exa-only verification items both enter the same deeper verification loop. Company-file update rows are informational/legacy; low-risk factual edits should be auto-applied and summarized in future runs.

## Priority Counts

- medium: 20

## Company File Updates / FYI

FYI or legacy proposed edits to existing company files. The target behavior is that low-risk factual updates are applied by a scoped writer and summarized here, while thesis/status-changing edits remain approval-gated.

| Priority | ID | Target | Verification | Suggested action | Why this is here / where to read | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| medium | HRQ-0002 | AAPL | not specified | FYI/legacy proposal. Future low-risk factual edits should be auto-applied and summarized, not approved here. | This is a legacy proposed company-file change. The target UX is auto-apply low-risk factual updates and summarize the edit for you. Update AAPL company news: Q2 2026 record results, 17% revenue growth, Q3 guidance 14-17% growth, and CEO transition news as reported by reliable sources. | [open evidence](agents/runs/2026-05-09_weekly/orchestrator_update_proposals.md#ORP-0001) |
| medium | HRQ-0003 | AAPL | source validated | FYI/legacy proposal. Future low-risk factual edits should be auto-applied and summarized, not approved here. | This is a legacy proposed company-file change. The target UX is auto-apply low-risk factual updates and summarize the edit for you. Update AAPL financial snapshot as-of 2026-05: price $284.2, market cap $4.157T, P/E 33.99, and other headline metrics from financial_compare, all source-validated and consistent. | [open evidence](agents/runs/2026-05-09_weekly/orchestrator_update_proposals.md#ORP-0002) |

## Monitoring Candidate Reviews

Source-backed discovery candidates that may be worth adding to monitoring after you review the linked evidence.

| Priority | ID | Target | Verification | Suggested action | Why this is here / where to read | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| medium | HRQ-0053 | AMKR | verified | Approve adding to monitoring, request more research, or reject/ignore. | Read the linked candidate group and market report first; approval means this source-backed lead may enter the monitoring approval path. Candidate surfaced from exa, grok with verification=verified, hype=unknown, cooldown=not_rejected. Tickers: AMKR. Source IDs are listed in the linked candidate review and market report. | [open evidence](agents/runs/2026-05-14_manual-market-ai-semiconductor-fresh/market_research/candidate_review.md#CRG-0001) |

## Grok/X Candidate Verification

Early social/X leads from Grok. Approving these only starts verification; it does not add them to monitoring.

| Priority | ID | Target | Verification | Suggested action | Why this is here / where to read | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| medium | HRQ-0004 | FLNC | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | This is a social/X lead only; approval means run verification, not add to monitoring. Candidate surfaced from grok with verification=grok_only, hype=high, cooldown=not_rejected. Tickers: FLNC. | [open evidence](agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0001) |
| medium | HRQ-0005 | NRGV | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | This is a social/X lead only; approval means run verification, not add to monitoring. Candidate surfaced from grok with verification=grok_only, hype=high, cooldown=not_rejected. Tickers: NRGV. | [open evidence](agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0002) |
| medium | HRQ-0006 | NXXT | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | This is a social/X lead only; approval means run verification, not add to monitoring. Candidate surfaced from grok with verification=grok_only, hype=high, cooldown=not_rejected. Tickers: NXXT. | [open evidence](agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0003) |
| medium | HRQ-0043 | ASX, INTC, LPK, RMBS | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | This is a social/X lead only; approval means run verification, not add to monitoring. Candidate surfaced from grok with verification=grok_only, hype=unknown, cooldown=not_rejected. Basket contains 4 tickers across 4 lead(s). Tickers: ASX, INTC, LPK, RMBS. | [open evidence](agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/candidate_review.md#CRG-0002) |
| medium | HRQ-0044 | GLW, KLAC, LRCX, ONTO, TSM | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | This is a social/X lead only; approval means run verification, not add to monitoring. Candidate surfaced from grok with verification=grok_only, hype=unknown, cooldown=not_rejected. Basket contains 5 tickers across 5 lead(s). Tickers: GLW, KLAC, LRCX, ONTO, TSM. | [open evidence](agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/candidate_review.md#CRG-0003) |
| medium | HRQ-0048 | CAMT, KLAC, ONTO | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | This is a social/X lead only; approval means run verification, not add to monitoring. Candidate surfaced from grok with verification=grok_only, hype=unknown, cooldown=not_rejected. Basket contains 3 tickers across 3 lead(s). Tickers: CAMT, KLAC, ONTO. Source IDs are listed in the linked candidate review and market report. | [open evidence](agents/runs/2026-05-14_manual-market-ai-semiconductor-fresh/market_research/candidate_review.md#CRG-0004) |
| medium | HRQ-0049 | ENTG, MKSI, ROG | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | This is a social/X lead only; approval means run verification, not add to monitoring. Candidate surfaced from grok with verification=grok_only, hype=unknown, cooldown=not_rejected. Basket contains 3 tickers across 3 lead(s). Tickers: ENTG, MKSI, ROG. Source IDs are listed in the linked candidate review and market report. | [open evidence](agents/runs/2026-05-14_manual-market-ai-semiconductor-fresh/market_research/candidate_review.md#CRG-0005) |
| medium | HRQ-0054 | AIXA, INTC, IQE, LPK, SOI, TSE | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | This is a social/X lead only; approval means run verification, not add to monitoring. Candidate surfaced from grok with verification=grok_only, hype=unknown, cooldown=not_rejected. Basket contains 6 tickers across 6 lead(s). Tickers: AIXA, INTC, IQE, LPK, SOI, TSE. Source IDs are listed in the linked candidate review and market report. | [open evidence](agents/runs/2026-05-14_manual-market-ai-semiconductor-fresh/market_research/candidate_review.md#CRG-0002) |
| medium | HRQ-0055 | AVGO, NVDA, TSM | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | This is a social/X lead only; approval means run verification, not add to monitoring. Candidate surfaced from grok with verification=grok_only, hype=unknown, cooldown=not_rejected. Basket contains 3 tickers across 3 lead(s). Tickers: AVGO, NVDA, TSM. Source IDs are listed in the linked candidate review and market report. | [open evidence](agents/runs/2026-05-14_manual-market-ai-semiconductor-fresh/market_research/candidate_review.md#CRG-0003) |
| medium | HRQ-0056 | FORM | grok only | Approve follow-up verification, reject/ignore, or leave open. Do not promote yet. | This is a social/X lead only; approval means run verification, not add to monitoring. Candidate surfaced from grok with verification=grok_only, hype=unknown, cooldown=not_rejected. Tickers: FORM. Source IDs are listed in the linked candidate review and market report. | [open evidence](agents/runs/2026-05-14_manual-market-ai-semiconductor-fresh/market_research/candidate_review.md#CRG-0006) |

## Candidate Verification

Leads that need more company/news/financial verification before any monitoring decision.

| Priority | ID | Target | Verification | Suggested action | Why this is here / where to read | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| medium | HRQ-0008 | CWEN | exa only | Approve follow-up verification or reject/ignore before any monitoring decision. | This lead needs company/news/financial verification before any monitoring decision. Candidate surfaced from exa with verification=exa_only, hype=unknown, cooldown=not_rejected. Tickers: CWEN. | [open evidence](agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0005) |
| medium | HRQ-0009 | IES.L | exa only | Approve follow-up verification or reject/ignore before any monitoring decision. | This lead needs company/news/financial verification before any monitoring decision. Candidate surfaced from exa with verification=exa_only, hype=unknown, cooldown=not_rejected. Tickers: IES.L. | [open evidence](agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md#CRG-0006) |
| medium | HRQ-0039 | WAF.DE | exa only | Approve follow-up verification or reject/ignore before any monitoring decision. | This lead needs company/news/financial verification before any monitoring decision. Candidate surfaced from exa with verification=exa_only, hype=high, cooldown=not_rejected. Tickers: WAF.DE. | [open evidence](agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/candidate_review.md#CRG-0004) |
| medium | HRQ-0040 | SOI.PA | exa only | Approve follow-up verification or reject/ignore before any monitoring decision. | This lead needs company/news/financial verification before any monitoring decision. Candidate surfaced from exa with verification=exa_only, hype=unknown, cooldown=not_rejected. Tickers: SOI.PA. | [open evidence](agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/candidate_review.md#CRG-0005) |
| medium | HRQ-0041 | SMHN.F | exa only | Approve follow-up verification or reject/ignore before any monitoring decision. | This lead needs company/news/financial verification before any monitoring decision. Candidate surfaced from exa with verification=exa_only, hype=unknown, cooldown=not_rejected. Tickers: SMHN.F. | [open evidence](agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/candidate_review.md#CRG-0006) |
| medium | HRQ-0042 | XFAB.PA | exa only | Approve follow-up verification or reject/ignore before any monitoring decision. | This lead needs company/news/financial verification before any monitoring decision. Candidate surfaced from exa with verification=exa_only, hype=unknown, cooldown=not_rejected. Tickers: XFAB.PA. | [open evidence](agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/candidate_review.md#CRG-0007) |

## Strategy / Workflow

Strategy or process changes that affect future runs.

| Priority | ID | Target | Verification | Suggested action | Why this is here / where to read | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| medium | HRQ-0001 | human-to-system intake | not specified | Approve, reject, or refine the workflow/strategy change. | This changes strategy or process; approve only if the workflow should remember it. Added from user request. | not linked |

## Suggested Codex Prompt

Tell Codex which HRQ ids to approve, reject, leave open, or mark as needing more research. Example:

`Approve HRQ-XXXX and HRQ-YYYY for follow-up verification; reject HRQ-ZZZZ; leave the rest open.`

Codex should record explicit decisions with `python -m stock_research human-review decide --set HRQ-XXXX=approved --write` before running any approved follow-up command.
