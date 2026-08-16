# Rejected State

Last updated: 2026-06-29

## Current View

- Rejected/inactive tracking now includes `KRKNF` after the user confirmed the Kraken Robotics position was sold.
- `KRKNF` is in cooldown until 2026-06-29 and should not resurface before then unless the user explicitly asks.

## Rejection Policy

- Rejected stocks should not resurface as candidates for 6 weeks after `date_rejected`.
- A rejected stock can be reviewed sooner only if the user explicitly overrides the cooldown.

## Important Changes Since Last Review

- 2026-05-18: Kraken Robotics was moved out of current holdings because the user sold the stock. Prior research was preserved in `stock_tracking/stock_info_files/rejected/KRKNF.md`.

## Reconsideration Queue

- None currently eligible. `KRKNF` next eligible review date is 2026-06-29.

## Common Rejection Patterns

- TODO: summarize recurring reasons stocks are being rejected.

## Planned Next Steps

- Respect `KRKNF` cooldown until 2026-06-29 unless the user explicitly asks for an earlier revisit.
- Keep the rejected-company file as historical context only; do not include `KRKNF` in current-holdings research runs.

## Open Questions

- TODO: capture missing information needed for the next review.

## Change Log

- 2026-04-30: Created initial state file template.
- 2026-05-18: Added `KRKNF` to rejected/inactive tracking after user-confirmed sale.

## Automated State Updates

| Date | Update ID | Category | Summary | Source |
| --- | --- | --- | --- | --- |
| 2026-05-16 | CATSTATE-2026-05-16_weekly | rejected | 0 rejected stock(s): 0 still in cooldown, 0 eligible for reconsideration. | [agents/runs/2026-05-16_weekly/final_digest.md](agents/runs/2026-05-16_weekly/final_digest.md) |
| 2026-05-18 | CATSTATE-2026-05-18_manual-lpkf-sivers-holdings | rejected | 1 rejected stock(s): 1 still in cooldown, 0 eligible for reconsideration. | [agents/runs/2026-05-18_manual-lpkf-sivers-holdings/run_summary.md](agents/runs/2026-05-18_manual-lpkf-sivers-holdings/run_summary.md) |
| 2026-05-19 | CATSTATE-2026-05-19_manual-penguin-solutions-monitoring | rejected | 1 rejected stock(s): 1 still in cooldown, 0 eligible for reconsideration. | [agents/runs/2026-05-19_manual-penguin-solutions-monitoring/final_digest.md](agents/runs/2026-05-19_manual-penguin-solutions-monitoring/final_digest.md) |
| 2026-05-30 | CATSTATE-2026-05-30_weekly | rejected | 1 rejected stock(s): 1 still in cooldown, 0 eligible for reconsideration. | [agents/runs/2026-05-30_weekly/final_digest.md](agents/runs/2026-05-30_weekly/final_digest.md) |
| 2026-06-06 | CATSTATE-2026-06-06_weekly | rejected | 1 rejected stock(s): 1 still in cooldown, 0 eligible for reconsideration. | [agents/runs/2026-06-06_weekly/final_digest.md](agents/runs/2026-06-06_weekly/final_digest.md) |
| 2026-06-13 | CATSTATE-2026-06-13_weekly | rejected | 1 rejected stock(s): 1 still in cooldown, 0 eligible for reconsideration. | [agents/runs/2026-06-13_weekly/final_digest.md](agents/runs/2026-06-13_weekly/final_digest.md) |
| 2026-06-29 | CATSTATE-2026-07-04_weekly | rejected | 1 rejected stock(s): 0 still in cooldown, 1 eligible for reconsideration. | [agents/runs/2026-07-04_weekly/final_digest.md](agents/runs/2026-07-04_weekly/final_digest.md) |

