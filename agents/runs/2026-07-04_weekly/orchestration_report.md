# Orchestration Report: 2026-07-04_weekly

Generated: 2026-06-29
Status: needs_review
Mode: providers_execute, analysis_execute, memory_writer_deterministic, orchestrator_not_run

## Step Summary

- manifest: written (107 provider task(s), 60 analysis task(s))
- provider_tasks: execute (107 executed, 0 error(s))
- analysis_tasks: execute (60 executed, 0 error(s), 0 skipped)
- quality_report: 1 finding(s)
- memory_finalization: complete
- memory_writer_review: deterministic_review
- company_file_factual_updates: blocked (12 item(s))
- category_state_updates: complete (3 item(s))
- company_research: not_run (0 ticker(s))
- final_digest: ready (12 ticker(s))
- human_synthesis_packs: ready (12 pack(s))
- human_review_digest: needs_user_review (6 open item(s))
- codex_review_pack: needs_review
- agent_orchestrator: not_run
- orchestrator_proposal_review: not_run

## SDK Quality Findings

- None.

## Artifacts

- `agents/runs/2026-07-04_weekly/manifest.json`
- `agents/runs/2026-07-04_weekly/run_summary.json`
- `agents/runs/2026-07-04_weekly/run_summary.md`
- `agents/runs/2026-07-04_weekly/company_file_factual_updates.md`
- `agents/runs/2026-07-04_weekly/final_digest.json`
- `agents/runs/2026-07-04_weekly/final_digest.md`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/AMBA_synthesis_pack.json`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/AMBA_synthesis_pack.md`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/AVAV_synthesis_pack.json`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/AVAV_synthesis_pack.md`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/AXTI_synthesis_pack.json`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/AXTI_synthesis_pack.md`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/GOOGL_synthesis_pack.json`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/GOOGL_synthesis_pack.md`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/IREN_synthesis_pack.json`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/IREN_synthesis_pack.md`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/LPK.DE_synthesis_pack.json`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/LPK.DE_synthesis_pack.md`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/MU_synthesis_pack.json`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/MU_synthesis_pack.md`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/NBIS_synthesis_pack.json`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/NBIS_synthesis_pack.md`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/OSS_synthesis_pack.json`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/OSS_synthesis_pack.md`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/PENG_synthesis_pack.json`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/PENG_synthesis_pack.md`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/SIVE.ST_synthesis_pack.json`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/SIVE.ST_synthesis_pack.md`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/TE_synthesis_pack.json`
- `agents/runs/2026-07-04_weekly/reports/human_synthesis/TE_synthesis_pack.md`
- `agents/human_review_digest.md`
- `stock_tracking/current_holdings/current_holdings_state.md`
- `stock_tracking/monitoring/monitoring_state.md`
- `stock_tracking/rejected/rejected_state.md`
- `agents/runs/2026-07-04_weekly/quality_report.json`
- `agents/runs/2026-07-04_weekly/quality_report.md`
- `agents/runs/2026-07-04_weekly/finalization.json`
- `agents/runs/2026-07-04_weekly/finalization.md`
- `agents/runs/2026-07-04_weekly/memory_writer_prompt.json`
- `agents/runs/2026-07-04_weekly/memory_writer_prompt.md`
- `agents/runs/2026-07-04_weekly/memory_writer_review.json`
- `agents/runs/2026-07-04_weekly/memory_writer_review.md`
- `agents/runs/2026-07-04_weekly/memory_update_drafts.json`
- `agents/runs/2026-07-04_weekly/memory_update_drafts.md`
- `agents/runs/2026-07-04_weekly/codex_supervised_review_pack.json`
- `agents/runs/2026-07-04_weekly/codex_supervised_review_pack.md`

## Next Actions

- Review `quality_report.md`; deterministic quality findings remain.
- Review `archive_proposals.md`; move eligible stale artifacts with `artifact-hygiene archive --write`.
- Review blocked company-file factual updates before accepting company-file sync.
- Codex app synthesis remains the next step in Codex-supervised mode; use `--execute-orchestrator` only for API-mode debugging or remote/headless fallback.
- Review `agents/human_review_digest.md` for pending approval/reject/more-research decisions.
- Resolve high-risk review gates for AMBA before updating the thesis.
- Resolve high-risk review gates for AXTI before updating the thesis.
- Resolve high-risk review gates for GOOGL before updating the thesis.
- Resolve high-risk review gates for IREN before updating the thesis.
- Resolve high-risk review gates for LPK.DE before updating the thesis.
- Resolve high-risk review gates for MU before updating the thesis.
- Resolve high-risk review gates for NBIS before updating the thesis.
- Resolve high-risk review gates for PENG before updating the thesis.
- Resolve high-risk review gates for SIVE.ST before updating the thesis.
- Resolve high-risk review gates for TE before updating the thesis.
- Review `agents/human_review_digest.md`: 6 open item(s) need approve/reject/more-research/leave-open decisions.
- Codex-supervised automation should read `agents/runs/2026-07-04_weekly/codex_supervised_review_pack.md`, write `agents/runs/2026-07-04_weekly/codex_supervised_review.md`, refresh every canonical `reports/human_synthesis/*_final_human_report.md` target, then run `python -m stock_research quality-report --run-id 2026-07-04_weekly --write --require-final-reports`.
