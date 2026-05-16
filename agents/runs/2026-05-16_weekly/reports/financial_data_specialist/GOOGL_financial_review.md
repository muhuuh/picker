# Financial Review: GOOGL

Status: needs_human_review
Reason: Material conflicts or low-confidence core metrics need review before file updates.

## Headline Metrics

| Metric | Value | Confidence | Providers |
| --- | --- | --- | --- |
| company_name | Alphabet Inc. | low | fmp, polygon |
| latest_price | 396.8 | high | fmp, polygon, yfinance |
| market_cap | 4.799e+12 | high | fmp, polygon, yfinance |
| pe_ratio | 29.97 | high | fmp, yfinance |
| price_to_sales_ttm | 11.36 | medium | fmp |
| ev_to_ebitda_ttm | 22.17 | medium | fmp |
| free_cash_flow_per_share_ttm | 5.325 | medium | fmp |
| debt_to_equity_ttm | 0.189 | medium | fmp |
| currency | USD | high | fmp, polygon, yfinance |
| exchange | NASDAQ | high | fmp, polygon, yfinance |
| sector | Communication Services | high | fmp, yfinance |
| industry | Internet Content & Information | high | fmp, yfinance |
| country | US | medium | fmp |

## Review Notes

- financial_compare packet: `agents/runs/2026-05-16_weekly/evidence_packets/2026-05-16_financial_compare_company_googl.json`
- confidence_counts: {"high": 7, "low": 1, "medium": 12}
- status_counts: {"conflict": 1, "consistent": 19}
- single_provider_metrics: country, debt_to_equity_ttm, ev_to_ebitda_ttm, fifty_two_week_high, fifty_two_week_low, free_cash_flow_per_share_ttm, previous_high, previous_low, previous_open, previous_volume, previous_vwap, price_to_sales_ttm
- missing_core_metrics: none
- low_confidence_core_metrics: company_name
- conflicts: 1
- material_conflicts: 1
- taxonomy_conflicts: 0

## Provider Conflicts

- company_name: material; Providers disagree after normalization.
  - values: {"fmp": "Alphabet Inc.", "polygon": "Alphabet Inc. Class A Common Stock"}
- recommended_company_file_action: Do not update financial conclusions until conflicts or low-confidence core metrics are reviewed.
