# Candidate Review: 2026-05-12_manual-market-ai-semiconductor-supply-chain

Generated: 2026-05-13
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

- agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/ai_semiconductor_supply_chain_advanced_packaging_candidate_leads.json

## Quality Findings

- None.

## Candidate Groups

| Group ID | Candidate | Evidence state | Decision options | Priority | Why it surfaced | Source IDs |
| --- | --- | --- | --- | --- | --- | --- |
| CRG-0001 | Amkor Technology, Inc. (AMKR) | channels=exa, grok; verification=verified; hype=unknown; cooldown=not_rejected | Approve adding this candidate to monitoring, or request more research first. | medium | Relevant Exa result: Amkor Technology, Inc.: Amkor Technology, Inc. (AMKR) is a Semiconductor Manufacturing company. Amkor Technology, Inc. Also surfaced because: Public: $INTC (EMIB push), $ASX (ASE, LEAP guidance raised >US$3.5B 2026, capex up), $LPK (LIDE TGV equipment leader), $AMKR (scaled OSAT), $RMBS (memory controllers). | exa_result_1, xai_x_source_1, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6 |
| CRG-0002 | EMIB/ASE/LEAP basket (ASX, INTC, LPK, RMBS) | channels=grok; verification=grok_only; hype=unknown; cooldown=not_rejected | Approve verification for this Grok/X basket, reject/ignore it, or request narrower research. | medium | Public: $INTC (EMIB push), $ASX (ASE, LEAP guidance raised >US$3.5B 2026, capex up), $LPK (LIDE TGV equipment leader), $AMKR (scaled OSAT), $RMBS (memory controllers). | xai_x_source_1, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6 |
| CRG-0003 | glass/inspection/etch basket (GLW, KLAC, LRCX, ONTO, TSM) | channels=grok; verification=grok_only; hype=unknown; cooldown=not_rejected | Approve verification for this Grok/X basket, reject/ignore it, or request narrower research. | medium | Others: $GLW (glass materials), $LRCX/$KLAC/$ONTO (inspection/etch), $TSM (CoWoS/CoPoS expansion), private KT&G (satirical but signals Samsung HBM yield dependency). | xai_x_source_1, xai_x_source_2, xai_x_source_3, xai_x_source_4, xai_x_source_5, xai_x_source_6 |
| CRG-0004 | Siltronic AG (WAF.DE) | channels=exa; verification=exa_only; hype=high; cooldown=not_rejected | Approve follow-up company and financial verification before considering monitoring. | medium | Relevant Exa result: Siltronic AG: Siltronic AG (WAF.DE) is a Semiconductor Manufacturing company. Siltronic AG is one of the world's leading producers of hyperpure silicon wafers and has been a partner to many major semiconductor manufacturers for decades. | exa_result_3 |
| CRG-0005 | Soitec (SOI.PA) | channels=exa; verification=exa_only; hype=unknown; cooldown=not_rejected | Approve follow-up company and financial verification before considering monitoring. | medium | Relevant Exa result: Soitec: Soitec (SOI.PA) is a Semiconductor Manufacturing company. Soitec is a world leader in innovative semiconductor materials. | exa_result_2 |
| CRG-0006 | SUSS (SMHN.F) | channels=exa; verification=exa_only; hype=unknown; cooldown=not_rejected | Approve follow-up company and financial verification before considering monitoring. | medium | Relevant Exa result: SUSS: SUSS (SMHN.F) is a Semiconductor Manufacturing company. SUSS MicroTec is a leading supplier of process equipment for microstructuring in the semiconductor industry and related markets with 70 years of engineering experience. | exa_result_5 |
| CRG-0007 | X-FAB (XFAB.PA) | channels=exa; verification=exa_only; hype=unknown; cooldown=not_rejected | Approve follow-up company and financial verification before considering monitoring. | medium | Relevant Exa result: X-FAB: X-FAB (XFAB.PA) is a Semiconductors company. X-FAB is a global foundry group providing a comprehensive set of specialty technologies and design IP to enable its customers to develop world-leading semiconductor products. | exa_result_4 |
