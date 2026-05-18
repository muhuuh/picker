# Human Review Digest

Generated: 2026-05-18
Status: needs_user_review
Open items summarized: 6

## Summary

- Monitoring Candidate Reviews: 1
- Grok/X Candidate Verification: 5

## Decision Options

- approve: allow the next gated follow-up step described in the row
- reject: close or ignore the item
- needs_more_research: keep open and request more evidence
- leave open: make no change

Monitoring candidates are not automatically added to monitoring. Grok/X and Exa-only verification items both enter the same deeper verification loop. Company-file update rows are informational/legacy; low-risk factual edits should be auto-applied and summarized in future runs.

## Priority Counts

- medium: 6

## Monitoring Candidate Reviews

Source-backed discovery candidates that may be worth adding to monitoring after you review the linked evidence.

| Priority | ID | Target | Verification | Suggested action | Why this is here / where to read | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| medium | HRQ-0053 | AMKR | verified | Approve adding to monitoring, request more research, or reject/ignore. | Monitoring-review candidate: approval starts the monitoring-addition path after evidence review. Candidate/group: Amkor Technology, Inc. (AMKR). Evidence state: channels=exa, grok; verification=verified; hype=unknown; cooldown=not_rejected. Why it surfaced: Relevant Exa result: Amkor Technology, Inc.: Amkor Technology, Inc. Amkor Technology, Inc. Amkor Technology, Inc. (Nasdaq: AMKR) is the world's largest U.S.-headquartered OSAT and is a global leader in outsourced semiconductor packaging and test services. Also surfaced because: OSATs: Amkor ($AMKR), ASE, FormFactor ($FORM). Decision expected: Approve adding this candidate to monitoring, or request more research first. Use the evidence link for source ids and the full market report before approving. | [open evidence](agents/runs/2026-05-14_manual-market-ai-semiconductor-fresh/market_research/candidate_review.md#CRG-0001) |

## Grok/X Candidate Verification

Early social/X leads from Grok. Approving these only starts verification; it does not add them to monitoring.

| Priority | ID | Target | Verification | Suggested action | Why this is here / where to read | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| medium | HRQ-0048 | CAMT, KLAC, ONTO | grok only | Verify, reject, or leave open. | Grok/X lead: approval only starts verification; it does not add the stock to monitoring. Candidate/group: Equipment basket (CAMT, KLAC, ONTO). Evidence state: channels=grok; verification=grok_only; hype=unknown; cooldown=not_rejected. Why it surfaced: Equipment: Towa (6315.T - HBM4 molding monopoly), Onto Innovation ($ONTO), Camtek ($CAMT), KLA ($KLAC), Applied Materials-adjacent. Decision expected: Approve verification for this Grok/X basket, reject/ignore it, or request narrower research. Use the evidence link for source ids and the full market report before approving. | [open evidence](agents/runs/2026-05-14_manual-market-ai-semiconductor-fresh/market_research/candidate_review.md#CRG-0004) |
| medium | HRQ-0049 | ENTG, MKSI, ROG | grok only | Verify, reject, or leave open. | Grok/X lead: approval only starts verification; it does not add the stock to monitoring. Candidate/group: Materials basket (ENTG, MKSI, ROG). Evidence state: channels=grok; verification=grok_only; hype=unknown; cooldown=not_rejected. Why it surfaced: Materials: Sumitomo Bakelite (4203.T - EME-G resin), Entrepia ($ENTG), MKS ($MKSI), Rogers ($ROG), ESI. Decision expected: Approve verification for this Grok/X basket, reject/ignore it, or request narrower research. Use the evidence link for source ids and the full market report before approving. | [open evidence](agents/runs/2026-05-14_manual-market-ai-semiconductor-fresh/market_research/candidate_review.md#CRG-0005) |
| medium | HRQ-0054 | AIXA, INTC, IQE, LPK, SOI, TSE | grok only | Verify, reject, or leave open. | Grok/X lead: approval only starts verification; it does not add the stock to monitoring. Candidate/group: Emerging basket (AIXA, INTC, IQE, LPK, SOI, TSE). Evidence state: channels=grok; verification=grok_only; hype=unknown; cooldown=not_rejected. Why it surfaced: Emerging: Intel ($INTC - EMIB), SK Hynix (EMIB testing), Tower Semiconductor ($TSE - silicon photonics), Soitec ($SOI - SOI wafers), IQE ($IQE - epiwafers), AIXTRON ($AIXA - MOCVD), LPKF ($LPK - glass processing), AP Memory (embedded capacitors). Decision expected: Approve verification for this Grok/X basket, reject/ignore it, or request narrower research. Use the evidence link for source ids and the full market report before approving. | [open evidence](agents/runs/2026-05-14_manual-market-ai-semiconductor-fresh/market_research/candidate_review.md#CRG-0002) |
| medium | HRQ-0055 | AVGO, NVDA, TSM | grok only | Verify, reject, or leave open. | Grok/X lead: approval only starts verification; it does not add the stock to monitoring. Candidate/group: Incumbents basket (AVGO, NVDA, TSM). Evidence state: channels=grok; verification=grok_only; hype=unknown; cooldown=not_rejected. Why it surfaced: Incumbents: TSMC ($TSM), Broadcom ($AVGO), Nvidia ($NVDA). Decision expected: Approve verification for this Grok/X basket, reject/ignore it, or request narrower research. Use the evidence link for source ids and the full market report before approving. | [open evidence](agents/runs/2026-05-14_manual-market-ai-semiconductor-fresh/market_research/candidate_review.md#CRG-0003) |
| medium | HRQ-0056 | FORM | grok only | Verify, reject, or leave open. | Grok/X lead: approval only starts verification; it does not add the stock to monitoring. Candidate/group: FORM (FORM). Evidence state: channels=grok; verification=grok_only; hype=unknown; cooldown=not_rejected. Why it surfaced: OSATs: Amkor ($AMKR), ASE, FormFactor ($FORM). Decision expected: Approve Exa/filing/financial verification of this Grok-only lead, or ignore it. Use the evidence link for source ids and the full market report before approving. | [open evidence](agents/runs/2026-05-14_manual-market-ai-semiconductor-fresh/market_research/candidate_review.md#CRG-0006) |

## Suggested Codex Prompt

Tell Codex which HRQ ids to approve, reject, leave open, or mark as needing more research. Example:

`Approve HRQ-XXXX and HRQ-YYYY for follow-up verification; reject HRQ-ZZZZ; leave the rest open.`

Codex should record explicit decisions with `python -m stock_research human-review decide --set HRQ-XXXX=approved --write` before running any approved follow-up command.
