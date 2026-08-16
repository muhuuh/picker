# Candidate Review: 2026-05-24_sheet-intake-soitec-soi

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

- agents/runs/2026-05-24_sheet-intake-soitec-soi/market_research/sheet_intake_candidate_leads.json

## Quality Findings

- None.

## Candidate Groups

| Group ID | Candidate | Evidence state | Decision options | Priority | Why it surfaced | Source IDs |
| --- | --- | --- | --- | --- | --- | --- |
| CRG-0001 | Soitec S.A. (SOI.PA) | channels=sheet; verification=unverified; hype=unknown; cooldown=not_rejected | Approve follow-up company and financial verification before considering monitoring. | medium | Soitec S.A. was added through the quick stock-intake sheet. Corrected from plain SOI to Soitec Euronext Paris ticker SOI.PA. Do not decide yet; complete research first. | sheet_row_12 |
