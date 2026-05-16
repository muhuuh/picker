# Financial Review: TE

Status: needs_human_review
Reason: Material conflicts or low-confidence core metrics need review before file updates.

## Headline Metrics

| Metric | Value | Confidence | Providers |
| --- | --- | --- | --- |
| company_name | T1 Energy Inc. | medium | polygon |
| latest_price | 5.67 | high | polygon, yfinance |
| market_cap | 1.599e+09 | high | polygon, yfinance |
| pe_ratio | 12.74 | medium | yfinance |
| currency | usd | high | polygon, yfinance |
| exchange | XNYS | low | polygon, yfinance |
| sector | Industrials | medium | yfinance |
| industry | Electrical Equipment & Parts | medium | yfinance |

## Review Notes

- financial_compare packet: `agents/runs/2026-05-16_weekly/evidence_packets/2026-05-16_financial_compare_company_te.json`
- confidence_counts: {"high": 3, "low": 1, "medium": 11}
- status_counts: {"conflict": 1, "consistent": 14}
- single_provider_metrics: company_name, fifty_two_week_high, fifty_two_week_low, industry, pe_ratio, previous_high, previous_low, previous_open, previous_volume, previous_vwap, sector
- missing_core_metrics: none
- low_confidence_core_metrics: exchange
- conflicts: 1
- material_conflicts: 1
- taxonomy_conflicts: 0

## Provider Conflicts

- exchange: material; Providers disagree after normalization.
  - values: {"polygon": "XNYS", "yfinance": "NYQ"}
- recommended_company_file_action: Do not update financial conclusions until conflicts or low-confidence core metrics are reviewed.
