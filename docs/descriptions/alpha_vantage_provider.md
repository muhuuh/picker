# Alpha Vantage Provider

Last updated: 2026-05-16

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
ALPHA_VANTAGE_API_KEY2="..." # optional fallback
```

The provider tries `ALPHA_VANTAGE_API_KEY` first. If Alpha Vantage returns a rate-limit, subscription/premium, or credential-style failure, the workflow retries once with `ALPHA_VANTAGE_API_KEY2` when configured. Secret values are never written to run artifacts; raw artifacts record only `primary`/`secondary` labels and sanitized error messages. If both keys fail, the provider still writes an explicit unavailable evidence packet so weekly runs continue with other financial providers.

## Workflow Role

Alpha Vantage should be used as a deterministic quote/overview cross-check for tracked stocks and human stock-research requests.

Use it carefully because free keys can be rate-limited. Statement pulls should be deliberate, not the default for every weekly run.

Implementation note: the provider spaces Alpha Vantage requests and retries once if the free-tier 1 request/second burst-limit message appears.

## Live Smoke Test

- 2026-05-04: AAPL live smoke test passed after adding request spacing/retry.
- Evidence packet: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_alpha_vantage_company_aapl.json`.
- Raw artifact: `agents/runs/2026-05-09_weekly/raw/alpha_vantage/AAPL_snapshot.json`.
- 2026-05-16: Official docs were rechecked for `GLOBAL_QUOTE` and `OVERVIEW`. The configured primary and secondary keys are present and the request shape is correct, but both returned Alpha Vantage standard daily/rate-limit messages during the smoke test. This should be treated as provider quota/coverage, not a malformed request.
