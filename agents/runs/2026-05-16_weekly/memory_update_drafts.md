# Memory Update Drafts: 2026-05-16_weekly

Generated: 2026-05-14

## Source Files

- `agents/runs/2026-05-16_weekly/memory_reflection.json`
- `agents/memory/recurring_failures.json`
- `agents/runs/2026-05-16_weekly/memory_writer_review.json`

## Draft Items

### proposal-2026-05-14-2026-05-16_weekly-reflection-issues

- action: memory_add
- target_file: evaluation_metrics.md
- status: ready
- reason: Ready draft passes deterministic validation.
- item_id: eval-2026-05-14-run-2026-05-16-weekly-produced-2-deterministic-r
- lesson: Run 2026-05-16_weekly produced 2 deterministic reflection issue(s). Review `memory_reflection.md`, run summary, quality report, and evidence packets before treating the run as complete.
- evidence: `agents/runs/2026-05-16_weekly/memory_reflection.md`

## Apply

Apply one approved proposal:

```powershell
python -m stock_research memory apply-updates --run-id 2026-05-16_weekly --proposal-id PROPOSAL_ID
```

Apply all ready proposals:

```powershell
python -m stock_research memory apply-updates --run-id 2026-05-16_weekly --all
```
