# Orchestration Report: 2026-05-16_weekly

Generated: 2026-05-16
Status: complete
Mode: providers_execute, analysis_execute, memory_writer_deterministic, orchestrator_not_run

## Step Summary

- manifest: written (81 provider task(s), 50 analysis task(s))
- provider_tasks: execute (81 executed, 0 error(s))
- analysis_tasks: execute (50 executed, 0 error(s), 0 skipped)
- quality_report: 0 finding(s)
- memory_finalization: complete
- memory_writer_review: deterministic_review
- company_file_factual_updates: complete (10 item(s))
- category_state_updates: complete (3 item(s))
- company_research: not_run (0 ticker(s))
- final_digest: ready (10 ticker(s))
- human_review_digest: needs_user_review (20 open item(s))
- codex_review_pack: ready
- agent_orchestrator: not_run
- orchestrator_proposal_review: not_run

## SDK Quality Findings

- None.

## Artifacts

- `agents/runs/2026-05-16_weekly/manifest.json`
- `agents/runs/2026-05-16_weekly/run_summary.json`
- `agents/runs/2026-05-16_weekly/run_summary.md`
- `agents/runs/2026-05-16_weekly/quality_report.json`
- `agents/runs/2026-05-16_weekly/quality_report.md`
- `agents/runs/2026-05-16_weekly/finalization.json`
- `agents/runs/2026-05-16_weekly/finalization.md`
- `agents/runs/2026-05-16_weekly/memory_writer_prompt.json`
- `agents/runs/2026-05-16_weekly/memory_writer_prompt.md`
- `agents/runs/2026-05-16_weekly/memory_writer_review.json`
- `agents/runs/2026-05-16_weekly/memory_writer_review.md`
- `agents/runs/2026-05-16_weekly/memory_update_drafts.json`
- `agents/runs/2026-05-16_weekly/memory_update_drafts.md`
- `agents/runs/2026-05-16_weekly/company_file_factual_updates.md`
- `agents/runs/2026-05-16_weekly/final_digest.json`
- `agents/runs/2026-05-16_weekly/final_digest.md`
- `agents/human_review_digest.md`
- `agents/runs/2026-05-16_weekly/codex_supervised_review_pack.json`
- `agents/runs/2026-05-16_weekly/codex_supervised_review_pack.md`

## Next Actions

- No deterministic learning-loop issues found.
- Review `company_file_factual_updates.md` for the FYI summary of factual company-file changes.
- OpenAI Agents SDK synthesis was not run. This is expected in Codex-supervised mode; use `--execute-orchestrator` only for API-mode benchmarking, debugging, or remote/headless execution.
- Review `agents/human_review_digest.md` for pending approve/reject/more-research decisions. These open items are normal asynchronous human decisions, not an automation failure.
- KRKNF remains a legitimate partial financial review because OTC/single-provider coverage is limited.
- Codex-supervised automation should read `agents/runs/2026-05-16_weekly/codex_supervised_review_pack.md` and write `agents/runs/2026-05-16_weekly/codex_supervised_review.md`.
