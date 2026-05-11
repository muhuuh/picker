# Financial Review: AMZN

Status: partial_review
Reason: No material numeric conflicts found, but some core metrics are missing or taxonomy labels differ by provider.

## Headline Metrics

| Metric | Value | Confidence | Providers |
| --- | --- | --- | --- |
| company_name | Amazon.com, Inc. | high | alpha_vantage, fmp, polygon |
| latest_price | 272.7 | high | alpha_vantage, fmp, polygon, yfinance |
| market_cap | 2.926e+12 | high | alpha_vantage, fmp, polygon, yfinance |
| pe_ratio | 32.18 | high | alpha_vantage, fmp, yfinance |
| price_to_sales_ttm | 3.939 | medium | fmp |
| ev_to_ebitda_ttm | 17.68 | medium | fmp |
| revenue_ttm | 7.428e+11 | medium | alpha_vantage |
| profit_margin | 0.122 | medium | alpha_vantage |
| eps | 8.37 | medium | alpha_vantage |
| free_cash_flow_per_share_ttm | -0.2301 | medium | fmp |
| debt_to_equity_ttm | 0.475 | medium | fmp |
| currency | USD | high | alpha_vantage, fmp, polygon, yfinance |
| exchange | NASDAQ | high | alpha_vantage, fmp, polygon, yfinance |
| sector | Consumer Cyclical | high | alpha_vantage, fmp, yfinance |
| industry | INTERNET RETAIL | medium | alpha_vantage, fmp, yfinance |
| country | US | high | alpha_vantage, fmp |

## Review Notes

- financial_compare packet: `agents/runs/2026-05-16_weekly/evidence_packets/2026-05-11_financial_compare_company_amzn.json`
- confidence_counts: {"high": 8, "medium": 17}
- status_counts: {"conflict": 1, "consistent": 24}
- single_provider_metrics: debt_to_equity_ttm, eps, ev_to_ebitda_ttm, fifty_two_week_high, fifty_two_week_low, free_cash_flow_per_share_ttm, peg_ratio, previous_high, previous_low, previous_open, previous_volume, previous_vwap, price_to_book_ratio, price_to_sales_ttm, profit_margin, revenue_ttm
- missing_core_metrics: none
- low_confidence_core_metrics: none
- conflicts: 1
- material_conflicts: 0
- taxonomy_conflicts: 1

## Provider Conflicts

- industry: taxonomy/watch; Providers disagree after normalization.
  - values: {"alpha_vantage": "INTERNET RETAIL", "fmp": "Specialty Retail", "yfinance": "Internet Retail"}
- recommended_company_file_action: Update available metrics, but preserve missing-core-metric notes for follow-up.
