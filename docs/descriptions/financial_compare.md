# Financial Compare

Last updated: 2026-05-04

## Purpose

`financial_compare` is the deterministic reconciliation layer for financial data.

It compares provider evidence packets for one ticker and writes a new provider-neutral evidence packet. This is intentionally limited to financial/profile/market-data evidence. Exa and xAI/Grok are excluded because they are for news, context, sentiment, and narrative discovery.

Implementation: `stock_research/financial_compare.py`.

## Current Tool

```powershell
python -m stock_research financial compare --ticker AAPL --run-id 2026-05-09_weekly
```

Optional explicit inputs:

```powershell
python -m stock_research financial compare --ticker AAPL --run-id 2026-05-09_weekly --packet agents\runs\2026-05-09_weekly\evidence_packets\PACKET.json
```

## Inputs

Financial provider packets:

- `yfinance`
- `fmp`
- `polygon`
- `alpha_vantage`
- `sec_edgar` when it contains extractable metrics

Excluded by design:

- `exa`
- `xai_grok`
- social/news/context packets

## Output

Raw comparison:

```text
agents/runs/{run_id}/raw/financial_compare/{TICKER}_comparison.json
```

Evidence packet:

```text
agents/runs/{run_id}/evidence_packets/{date}_financial_compare_company_{ticker}.json
```

## Comparison Rules

- Normalize provider-specific metric names into canonical metrics such as `latest_price`, `market_cap`, `pe_ratio`, `currency`, `exchange`, `sector`, and `industry`.
- Compare numeric values with metric-specific tolerances.
- Normalize harmless text differences such as casing, exchange aliases, country aliases, and company-name punctuation.
- Keep provider disagreements as contradictions instead of hiding them.
- Mark missing metrics in `unknowns`.
- Recommend company-file updates, with human review required only when material conflicts remain.

## Workflow Role

Financial comparison should run after provider tasks and before LLM synthesis.

```text
yfinance/FMP/Polygon/Alpha/SEC packets
  -> financial_compare packet
  -> financial-data specialist
  -> company research orchestrator
  -> company-file update proposal
```

Weekly manifests now include `analysis_tasks` for this post-provider step when tracked stocks or human stock-research requests exist.

## Live Smoke Test

- 2026-05-04: AAPL financial comparison passed.
- Evidence packet: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_financial_compare_company_aapl.json`.
- Raw artifact: `agents/runs/2026-05-09_weekly/raw/financial_compare/AAPL_comparison.json`.
