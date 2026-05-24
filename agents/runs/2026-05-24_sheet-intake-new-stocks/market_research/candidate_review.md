# Candidate Review: 2026-05-24_sheet-intake-new-stocks

Generated: 2026-05-24
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

- agents/runs/2026-05-24_sheet-intake-new-stocks/market_research/sheet_intake_candidate_leads.json

## Quality Findings

- None.

## Candidate Groups

| Group ID | Candidate | Evidence state | Decision options | Priority | Why it surfaced | Source IDs |
| --- | --- | --- | --- | --- | --- | --- |
| CRG-0001 | AIXA (AIXA) | channels=sheet; verification=unverified; hype=unknown; cooldown=not_rejected | Approve follow-up company and financial verification before considering monitoring. | medium | AIXA was added through the quick stock-intake sheet. | sheet_row_13 |
| CRG-0002 | AMBQ (AMBQ) | channels=sheet; verification=unverified; hype=unknown; cooldown=not_rejected | Approve follow-up company and financial verification before considering monitoring. | medium | AMBQ was added through the quick stock-intake sheet. | sheet_row_16 |
| CRG-0003 | ARM (ARM) | channels=sheet; verification=unverified; hype=unknown; cooldown=not_rejected | Approve follow-up company and financial verification before considering monitoring. | medium | ARM was added through the quick stock-intake sheet. | sheet_row_11 |
| CRG-0004 | FCEL (FCEL) | channels=sheet; verification=unverified; hype=unknown; cooldown=not_rejected | Approve follow-up company and financial verification before considering monitoring. | medium | FCEL was added through the quick stock-intake sheet. | sheet_row_15 |
| CRG-0005 | FLNC (FLNC) | channels=sheet; verification=unverified; hype=unknown; cooldown=not_rejected | Approve follow-up company and financial verification before considering monitoring. | medium | FLNC was added through the quick stock-intake sheet. | sheet_row_14 |
| CRG-0006 | LSCC (LSCC) | channels=sheet; verification=unverified; hype=unknown; cooldown=not_rejected | Approve follow-up company and financial verification before considering monitoring. | medium | LSCC was added through the quick stock-intake sheet. | sheet_row_17 |
| CRG-0007 | MRVL (MRVL) | channels=sheet; verification=unverified; hype=unknown; cooldown=not_rejected | Approve follow-up company and financial verification before considering monitoring. | medium | MRVL was added through the quick stock-intake sheet. | sheet_row_10 |
| CRG-0008 | OCC (OCC) | channels=sheet; verification=unverified; hype=unknown; cooldown=not_rejected | Approve follow-up company and financial verification before considering monitoring. | medium | OCC was added through the quick stock-intake sheet. | sheet_row_9 |
| CRG-0009 | SOI (SOI) | channels=sheet; verification=unverified; hype=unknown; cooldown=not_rejected | Approve follow-up company and financial verification before considering monitoring. | medium | SOI was added through the quick stock-intake sheet. | sheet_row_12 |
| CRG-0010 | VPG (VPG) | channels=sheet; verification=unverified; hype=unknown; cooldown=not_rejected | Approve follow-up company and financial verification before considering monitoring. | medium | VPG was added through the quick stock-intake sheet. | sheet_row_7 |
