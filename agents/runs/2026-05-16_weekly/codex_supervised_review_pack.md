# Codex-Supervised Review Pack: 2026-05-16_weekly

Status: needs_review
Expected Codex output: `agents/runs/2026-05-16_weekly/codex_supervised_review.md`

## Purpose

This pack is the deterministic handoff from Python to Codex app automation. The lower-cost scheduled workflow uses provider and analysis code to gather evidence, then asks Codex to synthesize, quality-check, and update repo memory/state without running the OpenAI API SDK orchestrator.

## Codex Instructions

1. Use Codex GPT-5.5 high as the outer orchestrator. Do not run the OpenAI API SDK orchestrator unless the user explicitly asks for API-mode benchmarking/debugging.
2. Read this review pack first, then read every existing required artifact and every opportunity assessment listed below.
3. Write or update the Codex-supervised final review at `agents/runs/2026-05-16_weekly/codex_supervised_review.md`. This file is the human-facing synthesis for the scheduled run.
4. The final review must include: bottom line, per-ticker attention ranking, material X/Grok narrative shifts, source-backed news, valuation/financial flags, non-obvious opportunities/risks, what changed vs existing company files, open human decisions, and next actions.
5. If a human-facing report is obviously poor, duplicated, truncated, stale, or missing key X/community insight, fix the relevant formatter/prompt/code and regenerate the affected report before finalizing.
6. Keep low-risk factual company-file updates as FYI. Do not ask for approval for routine source-backed factual syncs. Do ask for approval for thesis/status/strategy/buy/sell/position-size changes.
7. Do not make trades, do not silently move stocks between holdings/monitoring/rejected, and do not auto-approve human-review rows.
8. Review memory artifacts. If the run produced a durable operational lesson, update `agents/memory/` through the deterministic memory workflow or update the relevant scratchpad/backlog when that is the right scope.
9. Review artifact hygiene and category state updates. Preserve active reports, keep old inactive material discoverable through the archive index, and avoid cluttering active context with stale run artifacts.
10. End with a concise verdict: result quality, whether expectations were met, verification run, remaining risks, open human decisions, and the next backlog-driven step.

## Required Artifacts

| Status | Required | Artifact | Purpose |
| --- | --- | --- | --- |
| present | yes | `agents/runs/2026-05-16_weekly/final_digest.md` | Primary quick-read digest. Start here. |
| present | yes | `agents/runs/2026-05-16_weekly/quality_report.md` | Deterministic quality findings and provider/report coverage. |
| present | yes | `agents/runs/2026-05-16_weekly/run_summary.md` | Provider, evidence, and run coverage summary. |
| present | yes | `agents/runs/2026-05-16_weekly/finalization.md` | Run-end reflection, recurring issues, and archive proposals. |
| present | yes | `agents/human_review_digest.md` | Current user decision inbox. |
| present | no | `agents/runs/2026-05-16_weekly/company_file_factual_updates.md` | FYI summary of scoped factual company-file sync. |
| missing | no | `agents/runs/2026-05-16_weekly/category_state_updates.md` | FYI summary of holdings/monitoring/rejected state updates. |

## Opportunity Assessment Reports

| Status | Required | Artifact | Purpose |
| --- | --- | --- | --- |
| present | no | `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/AMBA_opportunity_assessment.md` | Human-facing deep company report. |
| present | no | `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/AVAV_opportunity_assessment.md` | Human-facing deep company report. |
| present | no | `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/AXTI_opportunity_assessment.md` | Human-facing deep company report. |
| present | no | `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/GOOGL_opportunity_assessment.md` | Human-facing deep company report. |
| present | no | `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/IREN_opportunity_assessment.md` | Human-facing deep company report. |
| present | no | `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/KRKNF_opportunity_assessment.md` | Human-facing deep company report. |
| present | no | `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/MU_opportunity_assessment.md` | Human-facing deep company report. |
| present | no | `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/NBIS_opportunity_assessment.md` | Human-facing deep company report. |
| present | no | `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/OSS_opportunity_assessment.md` | Human-facing deep company report. |
| present | no | `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/TE_opportunity_assessment.md` | Human-facing deep company report. |

## Human Review Artifacts

| Status | Required | Artifact | Purpose |
| --- | --- | --- | --- |
| present | yes | `agents/human_review_digest.md` | Primary open-decision digest. |
| present | yes | `agents/human_review_queue.md` | Durable review queue state. |
| missing | no | `agents/runs/2026-05-16_weekly/human_review_digest_summary.md` | Run-local review digest pointer. |

## Memory And Learning Artifacts

| Status | Required | Artifact | Purpose |
| --- | --- | --- | --- |
| present | yes | `agents/runs/2026-05-16_weekly/memory_reflection.md` | Post-run operational lessons and update proposals. |
| present | no | `agents/runs/2026-05-16_weekly/memory_update_drafts.md` | Schema-ready memory draft updates, if any. |
| present | no | `agents/runs/2026-05-16_weekly/memory_writer_review.md` | Deterministic or optional LLM review of memory drafts. |

## Hygiene And State Artifacts

| Status | Required | Artifact | Purpose |
| --- | --- | --- | --- |
| present | no | `agents/runs/2026-05-16_weekly/archive_proposals.md` | Run-local archive/hygiene proposals. |
| present | no | `archive/research_index.md` | Global generated-artifact index. |

## Quality Findings To Resolve Or Explain

- Human review digest may contain open decisions; Codex must summarize them clearly and not auto-approve them.

## API Workflow Benchmark

The OpenAI Agents SDK workflow remains available for remote/headless API mode and benchmarking:

```powershell
C:\Python313\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis --execute-orchestrator --orchestrator-timeout-seconds 900
```

Do not use API mode in the scheduled Codex-supervised automation unless the user explicitly asks for it.
