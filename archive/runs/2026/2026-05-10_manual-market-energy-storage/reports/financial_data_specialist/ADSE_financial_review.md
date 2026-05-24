# Financial Review: ADSE

Status: needs_human_review
Reason: Material conflicts or low-confidence core metrics need review before file updates.

## Headline Metrics

| Metric | Value | Confidence | Providers |
| --- | --- | --- | --- |
| company_name | Ads Tec Energy PLC | low | alpha_vantage, polygon |
| latest_price | 11.18 | high | alpha_vantage, polygon, yfinance |
| market_cap | 6.722e+08 | high | alpha_vantage, polygon, yfinance |
| pe_ratio | 13.56 | medium | yfinance |
| revenue_ttm | 3.156e+07 | medium | alpha_vantage |
| profit_margin | -1.749 | medium | alpha_vantage |
| eps | -1.08 | medium | alpha_vantage |
| currency | USD | high | alpha_vantage, polygon, yfinance |
| exchange | NASDAQ | medium | alpha_vantage, polygon, yfinance |
| sector | INDUSTRIALS | high | alpha_vantage, yfinance |
| industry | ELECTRICAL EQUIPMENT & PARTS | high | alpha_vantage, yfinance |
| country | USA | medium | alpha_vantage |

## Review Notes

- financial_compare packet: `agents/runs/2026-05-10_manual-market-energy-storage/evidence_packets/2026-05-11_financial_compare_company_adse.json`
- confidence_counts: {"high": 5, "low": 1, "medium": 15}
- status_counts: {"conflict": 2, "consistent": 19}
- single_provider_metrics: country, eps, fifty_two_week_high, fifty_two_week_low, pe_ratio, peg_ratio, previous_high, previous_low, previous_open, previous_volume, previous_vwap, price_to_book_ratio, profit_margin, revenue_ttm
- missing_core_metrics: none
- low_confidence_core_metrics: company_name
- conflicts: 2
- recommended_company_file_action: Do not update financial conclusions until conflicts or low-confidence core metrics are reviewed.
