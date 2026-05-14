# Orchestration Report: 2026-05-16_weekly

Generated: 2026-05-14
Status: needs_review
Mode: providers_execute, analysis_execute, memory_writer_deterministic, orchestrator_execute

## Step Summary

- manifest: written (19 provider task(s), 10 analysis task(s))
- provider_tasks: execute (17 executed, 2 error(s))
- analysis_tasks: execute (7 executed, 1 error(s), 2 skipped)
- quality_report: 2 finding(s)
- memory_finalization: needs_review
- memory_writer_review: deterministic_review
- company_research: complete (2 ticker(s))
- final_digest: ready (1 ticker(s))
- human_review_digest: needs_user_review (21 open item(s))
- agent_orchestrator: needs_review
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
- `agents/runs/2026-05-16_weekly/company_research/AMZN_company_research.json`
- `agents/runs/2026-05-16_weekly/company_research/AMZN_company_research.md`
- `agents/runs/2026-05-16_weekly/company_research/AMZN_company_research_metrics.md`
- `agents/runs/2026-05-16_weekly/company_research/AAPL_company_research.json`
- `agents/runs/2026-05-16_weekly/company_research/AAPL_company_research.md`
- `agents/runs/2026-05-16_weekly/company_research/AAPL_company_research_metrics.md`
- `agents/runs/2026-05-16_weekly/portfolio_review/portfolio_review.json`
- `agents/runs/2026-05-16_weekly/portfolio_review/portfolio_review.md`
- `agents/runs/2026-05-16_weekly/memory_evaluation/memory_evaluation.json`
- `agents/runs/2026-05-16_weekly/memory_evaluation/memory_evaluation.md`
- `agents/runs/2026-05-16_weekly/agent_runtime_main_orchestrator.json`
- `agents/runs/2026-05-16_weekly/agent_runtime_main_orchestrator.md`
- `agents/runs/2026-05-16_weekly/trace_links.md`
- `agents/runs/2026-05-16_weekly/run_metrics.md`
- `agents/runs/2026-05-16_weekly/final_digest.json`
- `agents/runs/2026-05-16_weekly/final_digest.md`
- `agents/human_review_digest.md`

## Next Actions

- Review provider task errors before treating the run as complete.
- Review analysis task errors/skips before synthesis.
- Review `quality_report.md`; deterministic quality findings remain.
- Review `memory_reflection.md` before treating the run as complete.
- Apply or reject proposed memory updates from `memory_reflection.md`.
- Review `memory_update_drafts.md` and apply approved ready drafts with `memory apply-updates`.
- Review portfolio review output before accepting final synthesis.
- Review memory/evaluation output before accepting the learning loop as complete.
- Review `agents/human_review_digest.md` for pending approval/reject/more-research decisions.
- Review `agents/human_review_digest.md`: 21 open item(s) need approve/reject/more-research/leave-open decisions.
