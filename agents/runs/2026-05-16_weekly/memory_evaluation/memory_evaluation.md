# Memory Evaluation: 2026-05-16_weekly

Status: needs_human_review

## Summary

Memory evaluation found 2 reflection issue(s), 0 recurring pattern(s), 1 draft memory update(s), and 0 SDK metric row(s).

## Metrics

- reflection issues: 2
- recurring patterns: 0
- memory update proposals: 1
- memory update drafts: 1
- ready memory update drafts: 1
- SDK metric rows: 0
- SDK timeouts: 0
- SDK errors: 0

## Artifacts

| Type | Status | Path | Summary |
| --- | --- | --- | --- |
| run_summary | present | agents/runs/2026-05-16_weekly/run_summary.md | summarizes deterministic run outputs |
| quality_report | present | agents/runs/2026-05-16_weekly/quality_report.md | deterministic evidence/source quality report |
| run_metrics | missing | agents/runs/2026-05-16_weekly/run_metrics.md | local SDK telemetry |
| memory_reflection | present | agents/runs/2026-05-16_weekly/memory_reflection.md | post-run memory reflection |
| memory_update_drafts | present | agents/runs/2026-05-16_weekly/memory_update_drafts.md | schema-valid memory update drafts |
| memory_writer_review | present | agents/runs/2026-05-16_weekly/memory_writer_review.md | bounded memory writer review |
| finalization | present | agents/runs/2026-05-16_weekly/finalization.md | run finalization summary |
| recurring_failures | present | agents/memory/recurring_failures.md | cross-run recurring failure report |

## Issues

- medium planned_provider_task_without_packet: Manifest task exa_news_company_aapl planned provider exa but no matching evidence packet was found.
- medium planned_provider_task_without_packet: Manifest task exa_company_search_company_aapl planned provider exa but no matching evidence packet was found.

## Next Actions

- Run SDK orchestration or accept that no SDK telemetry exists for this run.
- Review `memory_reflection.md` before treating the run as learning-loop complete.
- Review `memory_update_drafts.md`; apply only approved ready drafts with `memory apply-updates`.
- 1 memory draft(s) are ready for approval/application.
- Resolve finalization next actions before accepting this run as complete.
