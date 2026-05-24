# Run Artifact Retention Plan

## Goal

Make run learning scalable without keeping every generated file in the active repo surface.

## Scope

- Applies to generated artifacts under `agents/runs/`.
- Keeps durable learning in `agents/memory/`, `MEMORY.md`, stock files, category state, market research, strategy, human-review files, and archive indexes.
- Does not delete source-backed investment conclusions unless they have been promoted or preserved in markdown/indexed artifacts.

## Policy

- [x] Keep generated JSON ignored by Git.
- [x] Keep reviewable markdown summaries, final reports, quality reports, reflections, and finalization reports in Git or indexed archive.
- [x] Archive stale/inactive markdown with `artifact-hygiene archive`; do not delete markdown by default.
- [x] Clean ignored runtime JSON only with `artifact-hygiene cleanup-json`, dry-run first.
- [x] Block JSON cleanup when knowledge promotion, finalization, memory drafts, final human reports, review context/follow-up, retention age, Git-ignore, or Git tracking checks fail.
- [x] Use a commit hygiene boundary: stage durable state, archive moves, and review-linked/current markdown only; never stage generated run JSON.
- [ ] Periodically run cleanup after review days, then inspect `archive/runtime_cleanup_report.md`.

## File Retention Matrix

| File kind | Long-term handling |
| --- | --- |
| `*_final_human_report.md`, `codex_supervised_review.md`, `final_digest.md` | Keep while relevant; archive/index when stale. |
| `run_summary.md`, `quality_report.md`, `memory_reflection.md`, `finalization.md` | Keep as review trail; archive/index when stale. |
| Market/candidate verification markdown tied to open HRQ rows | Keep active until HRQ is resolved or superseded. |
| Specialist-lane markdown, synthesis packs, memory-writer prompts/reviews | Keep local/ignored by default; promote useful conclusions into final reports, candidate verification results, company files, or memory. |
| Old inactive markdown reports | Move to `archive/runs/` with `artifact-hygiene archive --write`. |
| Run-root JSON, raw provider JSON, evidence packet JSON, synthesis-pack JSON | Keep as local runtime cache; clean after promotion/finalization guardrails pass. |
| Operational lessons | Promote to `agents/memory/` through memory draft/apply flow or `memory add`. |
| Durable project decisions | Promote to `MEMORY.md`. |
| Investment facts and thesis changes | Promote to stock files, category state, market research, or strategy. |

## Current Findings: 2026-05-24

- Git tracks 122 `agents/runs` files, all Markdown; no run JSON is currently tracked.
- Local workspace has 542 ignored run JSON files, about 10 MB total.
- Local workspace has 139 run Markdown files, about 1 MB total.
- `artifact-hygiene inventory --today 2026-05-24 --archive-after-days 7` found 76 markdown artifacts: 42 active keeps, 4 recent keeps, 14 review-blocked, and 16 archive candidates.
- `artifact-hygiene cleanup-json --today 2026-05-24 --retention-days 30` found no cleanup candidates because all JSON-bearing runs are within default retention.
- `artifact-hygiene cleanup-json --today 2026-05-24 --retention-days 7` would plan cleanup for one finalized run, keep two recent runs, and block eight runs because they have open review context or missing finalization.
- `knowledge-promotion status --run-id 2026-05-19_manual-penguin-solutions-monitoring --today 2026-05-24` reports cleanup-ready promotion for the PENG run, with only an archive-index refresh warning.
- `artifact-hygiene cleanup-json --run-id 2026-05-19_manual-penguin-solutions-monitoring --retention-days 0 --today 2026-05-24` dry-runs 39 JSON files as eligible. No cleanup was executed.
- Cleanup execution: `artifact-hygiene cleanup-json --retention-days 0 --today 2026-05-24 --write` deleted 332 ignored runtime JSON files from `2026-05-16_weekly` and `2026-05-19_manual-penguin-solutions-monitoring` after promotion gates passed.
- Archive execution: `artifact-hygiene archive --archive-after-days 7 --today 2026-05-24 --write` moved 16 stale/inactive markdown artifacts into `archive/runs/` and refreshed `archive/research_index.md`.
- Post-cleanup state: 211 run JSON files remain because all remaining JSON-bearing runs are blocked by open HRQ references, missing finalization/quality/reflection artifacts, or the LPKF company-file promotion blocker.
- The cleanup flow exposed and fixed an order-safety issue: JSON cleanup now accepts required markdown artifacts that were already moved to `archive/runs/`, so archive-before-cleanup does not make a preserved run look unsafe.
- SIVE.ST from the 2026-05-18 LPKF/Sivers run was safely promoted with `company-file apply-factual-updates --ticker SIVE.ST --write`; LPK.DE remains blocked because the source assessment has unresolved quality findings.
- Commit hygiene check: current cleanup commit should preserve archive moves, final/review-linked PENG and Sheet-intake markdown, stock/memory/docs updates, and no generated JSON or specialist-lane markdown dumps.

## Next Steps

- [ ] Resolve or explicitly keep the LPK.DE promotion blocker before cleaning `2026-05-18_manual-lpkf-sivers-holdings` JSON.
- [ ] After the next Sunday review, dry-run `knowledge-promotion status --run-id RUN_ID`, `artifact-hygiene archive --archive-after-days 14`, and `artifact-hygiene cleanup-json --retention-days 14`.
- [ ] Resolve or supersede old HRQ rows that keep stale market reports active.
- [ ] Consider a scheduled monthly dry-run report before enabling any automatic `--write` cleanup.
