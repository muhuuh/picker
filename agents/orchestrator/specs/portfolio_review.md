# Portfolio Review Orchestrator Spec

## Purpose

Review the portfolio/watchlist state across current holdings, monitoring, rejected cooldowns, open approvals, and recent verification outputs.

## Inputs

- `stock_tracking/current_holdings/current_holdings.csv`
- `stock_tracking/monitoring/monitoring.csv`
- `stock_tracking/rejected/rejected.csv`
- `agents/human_review_queue.md`
- `agents/human_review_digest.md`
- run artifacts under `agents/runs/{run_id}/`
- operational memory from `agents/memory/`

## Outputs

- structured `OrchestratorDecision`
- alerts for stale or risky portfolio state
- human-review items for approval-gated decisions
- next-run tasks for stale rows, missing files, open approvals, and verification gaps

## Guardrails

- No direct trading instructions.
- No automatic stock status moves.
- No company-file edits.
- No promotion of discovery candidates without explicit human approval and verification gates.
