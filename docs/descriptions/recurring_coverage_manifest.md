# Recurring Coverage Manifest

Last updated: 2026-08-16

## Purpose

The recurring portfolio update needs an explicit, inspectable answer to four questions before providers run:

1. Which companies are in scope, and why?
2. Which portfolio-relevant industries should be researched once for all affected companies?
3. Which provider owns each research lane?
4. Which explicitly accepted run, if any, is the comparison baseline?

`stock_research/recurring_coverage.py` builds this contract and stores it under `recurring_coverage` in the weekly manifest. It is planning metadata, not another research agent and not a replacement for specialist evidence.

## Scope And State Boundaries

- `stock_tracking/current_holdings/current_holdings.csv` and `stock_tracking/monitoring/monitoring.csv` define recurring company membership.
- Rejected stocks and Google Sheet `new_stock_overview` ideas are excluded. The Sheet remains an intake inbox until an explicit approved workflow changes repo state.
- `strategy/portfolio_industry_coverage.json` maps tracked tickers to stable, deduplicated portfolio-industry clusters. It does not add companies to recurring scope.
- A future tracked ticker without a configured mapping receives a deterministic fallback cluster from its CSV `industry`, then `sector`, rather than disappearing from coverage.
- The builder is read-only. It does not change holdings, monitoring, rejected, strategy priorities, or company files.

Portfolio weights are not stored. `impact_basis: membership_only` and `weights_available: false` prohibit ranking exposure or concentration from row order, price, or market capitalization.

## Company And Industry Coverage

Each tracked company records:

- membership bucket and CSV path;
- a concrete coverage reason;
- CSV sector and industry;
- one or more portfolio-industry cluster ids;
- metadata, filing, news, and sentiment freshness status.

Freshness describes dates recorded in repo CSV metadata only. It does not prove that a live provider task succeeded. Dates are classified as `unknown`, `invalid_date`, `future_date`, `within_recurring_window`, or `stale` against the 14-day recurring window.

Industry clusters record their member tickers, themes, source industries, mapping source, and focused Exa/Grok topics. Overlapping companies can belong to multiple clusters, but each material cluster creates only:

- one Exa industry/news task with an explicit 21-day publication window; and
- one Grok 4.6 `x_search` industry pulse with a 21-day X window.

Company Exa news tasks use an explicit 14-day publication window. The dates are derived from the scheduled run date so repeated manifest builds are deterministic.

## Provider Roles

- Financial providers: normalized market-data snapshots and deterministic cross-checks.
- SEC EDGAR and company investor relations: official filings and company facts.
- Exa: current web/news discovery, primary-source finding, and selected contents retrieval.
- xAI Grok 4.6 `x_search`: X-native expert/community narratives, disagreement, rumors, and emerging signals.
- Grok `web_search`: deferred auxiliary gap filling only. It lives in `deferred_provider_tasks`, is not executed by the normal provider runner, and requires an identified coverage gap plus independent verification of material facts.

## Accepted Comparison Baseline

`agents/recurring_research_state.json` records the accepted portfolio-update run separately from generated run directories. The policy is `explicit_acceptance_only`:

- an empty pointer yields `not_recorded`;
- a pointer whose active or archived run directory is missing yields `recorded_artifact_missing`;
- only a present explicitly recorded run yields `accepted` and a non-empty `comparison_run_id`.

The newest generated weekly run is reported for transparency, but it is never substituted for an accepted run. The initial state intentionally has no accepted baseline because no report has yet been accepted under this new recurring contract.

## Reader Handoff

`run_summary.md` includes a compact recurring-coverage section with company and cluster counts, cluster membership, impact basis, accepted baseline status, and latest generated run. `codex_supervised_review_pack.md` requires the manifest and instructs the final synthesizer to use the coverage reasons, cluster plan, freshness, provider roles, and accepted baseline.

This slice establishes coverage and planning. Deterministic claim-level change detection, cross-company read-through synthesis, materiality-triggered deep reports, and the final executive report remain later backlog work.
