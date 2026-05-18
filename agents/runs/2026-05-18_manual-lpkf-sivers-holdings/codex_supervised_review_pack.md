# Codex-Supervised Review Pack: 2026-05-18_manual-lpkf-sivers-holdings

Status: ready
Expected Codex output: `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/codex_supervised_review.md`
Post-Codex quality gate: `python -m stock_research quality-report --run-id 2026-05-18_manual-lpkf-sivers-holdings --write --require-final-reports`

## Purpose

This pack is the deterministic handoff from Python to Codex app automation. The lower-cost scheduled workflow uses provider and analysis code to gather evidence, then asks Codex to synthesize, quality-check, and update repo memory/state without running the OpenAI API SDK orchestrator.

## Codex Instructions

1. Use Codex GPT-5.5 high as the outer orchestrator. Do not run the OpenAI API SDK orchestrator unless the user explicitly asks for remote/headless fallback or SDK debugging.
2. Read this review pack first, then read every existing required artifact and every human synthesis pack listed below. Use opportunity assessments as audit/evidence artifacts, not as final prose to patch together.
3. Write or update the Codex-supervised final review at `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/codex_supervised_review.md`. This file is the human-facing synthesis for the scheduled run.
4. For every human synthesis pack, write or refresh the matching canonical `reports/human_synthesis/{TICKER}_final_human_report.md` target from first principles. This is the reader-facing company/opportunity report; `reports/opportunity_assessment/` is the deterministic audit trail.
5. Do not create separate side reports, alternate report names, or chat-only report artifacts for automation-style stock research. If a report needs correction, overwrite the same canonical final human report target.
6. Each final human report should include: bottom line, business context, what changed, material X/Grok narrative shifts, source-backed news, valuation/financial flags, non-obvious opportunities/risks, what changed vs existing company files, open human decisions, and next actions.
7. If a human-facing report is obviously poor, duplicated, over-compressed, stale, or missing key X/Grok/web insight, fix the synthesis pack, formatter, prompt, or provider coverage and regenerate the affected artifact before finalizing.
8. After writing `codex_supervised_review.md` and all final human reports, run `python -m stock_research quality-report --run-id 2026-05-18_manual-lpkf-sivers-holdings --write --require-final-reports`. Do not finish the supervised run while it reports missing, orphaned, shallow, or malformed final human reports.
9. Keep low-risk factual company-file updates as FYI. Do not ask for approval for routine source-backed factual syncs. Do ask for approval for thesis/status/strategy/buy/sell/position-size changes.
10. Do not make trades, do not silently move stocks between holdings/monitoring/rejected, and do not auto-approve human-review rows.
11. Review memory artifacts. If the run produced a durable operational lesson, update `agents/memory/` through the deterministic memory workflow or update the relevant scratchpad/backlog when that is the right scope.
12. Review artifact hygiene and category state updates. Preserve active reports, keep old inactive material discoverable through the archive index, and avoid cluttering active context with stale run artifacts.
13. End with a concise verdict: result quality, whether expectations were met, verification run, remaining risks, open human decisions, and the next backlog-driven step.

## Required Artifacts

| Status | Required | Artifact | Purpose |
| --- | --- | --- | --- |
| present | yes | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/final_digest.md` | Primary quick-read digest. Start here. |
| present | yes | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/quality_report.md` | Deterministic quality findings and provider/report coverage. |
| present | yes | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/run_summary.md` | Provider, evidence, and run coverage summary. |
| present | yes | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/finalization.md` | Run-end reflection, recurring issues, and archive proposals. |
| present | yes | `agents/human_review_digest.md` | Current user decision inbox. |
| missing | no | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/company_file_factual_updates.md` | FYI summary of scoped factual company-file sync. |
| missing | no | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/category_state_updates.md` | FYI summary of holdings/monitoring/rejected state updates. |

## Human Synthesis Packs

| Status | Required | Artifact | Purpose |
| --- | --- | --- | --- |
| present | no | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/reports/human_synthesis/LPK.DE_synthesis_pack.md` | Codex app final-report evidence pack. |
| present | no | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/reports/human_synthesis/SIVE.ST_synthesis_pack.md` | Codex app final-report evidence pack. |

## Final Human Report Targets

| Status | Required | Artifact | Purpose |
| --- | --- | --- | --- |
| present | no | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/reports/human_synthesis/LPK.DE_final_human_report.md` | Codex app-written per-ticker final report. |
| present | no | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/reports/human_synthesis/SIVE.ST_final_human_report.md` | Codex app-written per-ticker final report. |

After Codex writes or refreshes those targets, rerun the post-Codex quality gate. It must be clean before the run is treated as complete.

## Opportunity Assessment Reports

| Status | Required | Artifact | Purpose |
| --- | --- | --- | --- |
| present | no | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/reports/opportunity_assessment/LPK.DE_opportunity_assessment.md` | Deterministic opportunity audit trail. |
| present | no | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/reports/opportunity_assessment/SIVE.ST_opportunity_assessment.md` | Deterministic opportunity audit trail. |

## Human Review Artifacts

| Status | Required | Artifact | Purpose |
| --- | --- | --- | --- |
| present | yes | `agents/human_review_digest.md` | Primary open-decision digest. |
| present | yes | `agents/human_review_queue.md` | Durable review queue state. |
| present | no | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/human_review_digest_summary.md` | Run-local review digest pointer. |

## Memory And Learning Artifacts

| Status | Required | Artifact | Purpose |
| --- | --- | --- | --- |
| present | yes | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/memory_reflection.md` | Post-run operational lessons and update proposals. |
| present | no | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/memory_update_drafts.md` | Schema-ready memory draft updates, if any. |
| missing | no | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/memory_writer_review.md` | Deterministic or optional LLM review of memory drafts. |

## Hygiene And State Artifacts

| Status | Required | Artifact | Purpose |
| --- | --- | --- | --- |
| present | no | `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/archive_proposals.md` | Run-local archive/hygiene proposals. |
| present | no | `archive/research_index.md` | Global generated-artifact index. |

## Quality Findings To Resolve Or Explain

- None detected by the deterministic review-pack builder.

## API Workflow Fallback

The OpenAI Agents SDK workflow remains available for remote/headless API mode, traces, and debugging when Codex app supervision is unavailable:

```powershell
C:\Python313\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis --execute-orchestrator --orchestrator-timeout-seconds 900
```

Do not use API mode in the scheduled Codex-supervised automation unless the user explicitly asks for remote/headless fallback or SDK debugging.
