# Financial Review: AAPL

Status: ready_for_company_update
Reason: Core metrics are available and no material provider conflicts were found.

## Headline Metrics

| Metric | Value | Confidence | Providers |
| --- | --- | --- | --- |
| company_name | Apple Inc. | high | alpha_vantage, fmp, polygon |
| latest_price | 280.1 | high | alpha_vantage, fmp, polygon, yfinance |
| market_cap | 4.114e+12 | high | alpha_vantage, fmp, polygon, yfinance |
| pe_ratio | 33.63 | high | alpha_vantage, fmp, yfinance |
| price_to_sales_ttm | 9.114 | medium | fmp |
| ev_to_ebitda_ttm | 25.39 | medium | fmp |
| revenue_ttm | 4.514e+11 | medium | alpha_vantage |
| profit_margin | 0.272 | medium | alpha_vantage |
| eps | 8.26 | medium | alpha_vantage |
| free_cash_flow_per_share_ttm | 8.781 | medium | fmp |
| debt_to_equity_ttm | 0.01875 | medium | fmp |
| currency | USD | high | alpha_vantage, fmp, polygon, yfinance |
| exchange | NASDAQ | high | alpha_vantage, fmp, polygon, yfinance |
| sector | Technology | high | alpha_vantage, fmp, yfinance |
| industry | Consumer Electronics | high | alpha_vantage, fmp, yfinance |
| country | US | high | alpha_vantage, fmp |

## Review Notes

- financial_compare packet: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_financial_compare_company_aapl.json`
- confidence_counts: {"high": 9, "medium": 16}
- status_counts: {"consistent": 25}
- single_provider_metrics: debt_to_equity_ttm, eps, ev_to_ebitda_ttm, fifty_two_week_high, fifty_two_week_low, free_cash_flow_per_share_ttm, peg_ratio, previous_high, previous_low, previous_open, previous_volume, previous_vwap, price_to_book_ratio, price_to_sales_ttm, profit_margin, revenue_ttm
- missing_core_metrics: none
- low_confidence_core_metrics: none
- conflicts: 0
- recommended_company_file_action: Update the company file financial snapshot from the review packet.
