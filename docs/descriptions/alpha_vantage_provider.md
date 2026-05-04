# Alpha Vantage Provider

Last updated: 2026-05-04

## Purpose

Alpha Vantage is used as a fallback and cross-check provider for quote, overview, and optional statement data.

Implementation: `stock_research/providers/alpha_vantage.py`.

## Official Sources Reviewed

- Alpha Vantage docs: https://www.alphavantage.co/documentation/

Relevant endpoints:

- `GLOBAL_QUOTE`
- `OVERVIEW`
- `INCOME_STATEMENT`
- `BALANCE_SHEET`
- `CASH_FLOW`
- `EARNINGS`

## Current Tool

```powershell
python -m stock_research alpha-vantage company --ticker AAPL --run-id 2026-05-09_weekly
```

Optional heavier pull:

```powershell
python -m stock_research alpha-vantage company --ticker AAPL --run-id 2026-05-09_weekly --include-statements
```

## Configuration

```text
ALPHA_VANTAGE_API_KEY="..."
```

## Workflow Role

Alpha Vantage should be used as a deterministic quote/overview cross-check for tracked stocks and human stock-research requests.

Use it carefully because free keys can be rate-limited. Statement pulls should be deliberate, not the default for every weekly run.

Implementation note: the provider spaces Alpha Vantage requests and retries once if the free-tier 1 request/second burst-limit message appears.

## Live Smoke Test

- 2026-05-04: AAPL live smoke test passed after adding request spacing/retry.
- Evidence packet: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_alpha_vantage_company_aapl.json`.
- Raw artifact: `agents/runs/2026-05-09_weekly/raw/alpha_vantage/AAPL_snapshot.json`.
