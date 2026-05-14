# Candidate Review: 2026-05-14_manual-market-ai-semiconductor-fresh

Generated: 2026-05-14
Status: ready_for_human_review

## Purpose

This file is the evidence bridge behind candidate rows in `agents/human_review_digest.md`. It groups market-discovery leads so you can decide what Codex should do next. It does not add stocks to monitoring.

## How To Use This File

- Read this when the human review digest links to a candidate group.
- HRQ means Human Review Queue id. Use the HRQ id from `agents/human_review_digest.md` when telling Codex what to do; the CRG id in this file is the evidence group behind that HRQ row.
- Tell Codex the HRQ id or group id and one decision: approve verification, approve monitoring review, reject, or needs_more_research.
- Verification means collect deeper company/news/financial evidence first. Monitoring review means the lead already has enough source support to consider adding it to monitoring.
- Source IDs map to the Sources section in the linked market research report; this file is a concise triage view, not the full source bibliography.

## Source Files

- agents/runs/2026-05-14_manual-market-ai-semiconductor-fresh/market_research/ai_semiconductor_supply_chain_advanced_packaging_fresh_candidate_leads.json

## Quality Findings

- None.

## Candidate Groups

| Group ID | Candidate | Evidence state | Decision options | Priority | Why it surfaced | Source IDs |
| --- | --- | --- | --- | --- | --- | --- |
| CRG-0001 | Amkor Technology, Inc. (AMKR) | channels=exa, grok; verification=verified; hype=unknown; cooldown=not_rejected | Approve adding this candidate to monitoring, or request more research first. | medium | Relevant Exa result: Amkor Technology, Inc.: Amkor Technology, Inc. Amkor Technology, Inc. Amkor Technology, Inc. (Nasdaq: AMKR) is the world's largest U.S.-headquartered OSAT and is a global leader in outsourced semiconductor packaging and test services. Also surfaced because: OSATs: Amkor ($AMKR), ASE, FormFactor ($FORM). | exa_result_5_f09da05f1c, xai_x_source_1, xai_x_source_10, xai_x_source_11, xai_x_source_12, xai_x_source_13, xai_x_source_14, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6, xai_x_source_7, xai_x_source_8, xai_x_source_9 |
| CRG-0002 | Emerging basket (AIXA, INTC, IQE, LPK, SOI, TSE) | channels=grok; verification=grok_only; hype=unknown; cooldown=not_rejected | Approve verification for this Grok/X basket, reject/ignore it, or request narrower research. | medium | Emerging: Intel ($INTC - EMIB), SK Hynix (EMIB testing), Tower Semiconductor ($TSE - silicon photonics), Soitec ($SOI - SOI wafers), IQE ($IQE - epiwafers), AIXTRON ($AIXA - MOCVD), LPKF ($LPK - glass processing), AP Memory (embedded capacitors). | xai_x_source_1, xai_x_source_10, xai_x_source_11, xai_x_source_12, xai_x_source_13, xai_x_source_14, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6, xai_x_source_7, xai_x_source_8, xai_x_source_9 |
| CRG-0003 | Incumbents basket (AVGO, NVDA, TSM) | channels=grok; verification=grok_only; hype=unknown; cooldown=not_rejected | Approve verification for this Grok/X basket, reject/ignore it, or request narrower research. | medium | Incumbents: TSMC ($TSM), Broadcom ($AVGO), Nvidia ($NVDA). | xai_x_source_1, xai_x_source_10, xai_x_source_11, xai_x_source_12, xai_x_source_13, xai_x_source_14, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6, xai_x_source_7, xai_x_source_8, xai_x_source_9 |
| CRG-0004 | Equipment basket (CAMT, KLAC, ONTO) | channels=grok; verification=grok_only; hype=unknown; cooldown=not_rejected | Approve verification for this Grok/X basket, reject/ignore it, or request narrower research. | medium | Equipment: Towa (6315.T - HBM4 molding monopoly), Onto Innovation ($ONTO), Camtek ($CAMT), KLA ($KLAC), Applied Materials-adjacent. | xai_x_source_1, xai_x_source_10, xai_x_source_11, xai_x_source_12, xai_x_source_13, xai_x_source_14, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6, xai_x_source_7, xai_x_source_8, xai_x_source_9 |
| CRG-0005 | Materials basket (ENTG, MKSI, ROG) | channels=grok; verification=grok_only; hype=unknown; cooldown=not_rejected | Approve verification for this Grok/X basket, reject/ignore it, or request narrower research. | medium | Materials: Sumitomo Bakelite (4203.T - EME-G resin), Entrepia ($ENTG), MKS ($MKSI), Rogers ($ROG), ESI. | xai_x_source_1, xai_x_source_10, xai_x_source_11, xai_x_source_12, xai_x_source_13, xai_x_source_14, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6, xai_x_source_7, xai_x_source_8, xai_x_source_9 |
| CRG-0006 | FORM (FORM) | channels=grok; verification=grok_only; hype=unknown; cooldown=not_rejected | Approve Exa/filing/financial verification of this Grok-only lead, or ignore it. | medium | OSATs: Amkor ($AMKR), ASE, FormFactor ($FORM). | xai_x_source_1, xai_x_source_10, xai_x_source_11, xai_x_source_12, xai_x_source_13, xai_x_source_14, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6, xai_x_source_7, xai_x_source_8, xai_x_source_9 |
