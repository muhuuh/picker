# Research Profiles And State Boundaries

Last updated: 2026-08-16

## Purpose

Research intent and durable portfolio state are separate concerns. Asking for research must not silently add a stock to monitoring, create a recurring industry priority, alter a thesis, or imply a trade decision.

The importable contracts live in `stock_research/research_profiles.py`.

## Profiles

| Profile | Purpose | Normal output | State boundary |
| --- | --- | --- | --- |
| `portfolio_update` | Recurring delta-first holdings, monitoring, and portfolio-industry update | `reports/portfolio_update/portfolio_executive_update.md` | May update factual/category summaries, but not portfolio membership or strategy |
| `company_deep_research` | On-demand company research | `reports/company_deep_research/{subject_id}_deep_research.md` | Run artifacts and report only; no monitoring/holding/rejected mutation |
| `industry_deep_research` | On-demand industry or theme research | `reports/industry_deep_research/{subject_id}_deep_research.md` | Does not create a recurring strategy priority |
| `candidate_discovery` | Discovery and approval-gated verification | `market_research/{subject_id}_manual_market_research.md` | Leads remain outside monitoring until verified and explicitly approved |

Each profile declares:

- supported subject types;
- default research window;
- provider lanes;
- depth;
- output contract;
- materiality rules;
- write permissions.

`build_research_run_spec(...)` validates a profile/subject combination and snapshots the full contract into `agents/runs/{run_id}/research_run_spec.json`. Downstream workflows should consume that snapshot rather than infer permissions from a generic run label.

## Request Routing

`python -m stock_research route-request "Research ASML"` remains the compatibility command, but its safe behavior is now:

1. append the request to the human input queue;
2. create a `company_deep_research` run spec;
3. leave holdings, monitoring, rejected, strategy, and company files unchanged.

The default queue status is `planned_on_demand`, which keeps the request out of the overloaded recurring manifest. An explicit `--status` override remains available for compatibility or deliberate scheduling.

An industry or theme request can create the requested research stub and an `industry_deep_research` run spec, but it does not become recurring unless the user separately asks for recurring coverage or a strategy change.

Portfolio membership changes remain explicit approval/status workflows. Candidate promotion remains the existing verified and approval-gated `candidate-promote` path.

## Guardrails

- Check `write_permissions` inside each writer before it creates directories or files. `write_research_run_spec(...)` enforces `run_artifacts`, and the compatibility industry-report writer enforces `reader_reports` before writing.
- A report recommendation is not permission to mutate state.
- Preserve the original user question in the run spec.
- CLI commands should call the importable profile/spec functions rather than reimplement profile logic.
- Compatibility means old commands keep routing; it does not mean unsafe side effects remain.
