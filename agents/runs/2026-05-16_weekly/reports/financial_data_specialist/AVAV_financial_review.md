# Financial Review: AVAV

Status: needs_human_review
Reason: Material conflicts or low-confidence core metrics need review before file updates.

## Headline Metrics

| Metric | Value | Confidence | Providers |
| --- | --- | --- | --- |
| company_name | AeroVironment, Inc. | medium | polygon |
| latest_price | 158 | high | polygon, yfinance |
| market_cap | 8.364e+09 | low | polygon, yfinance |
| pe_ratio | 39.01 | medium | yfinance |
| currency | usd | high | polygon, yfinance |
| exchange | XNAS | high | polygon, yfinance |
| sector | Industrials | medium | yfinance |
| industry | Aerospace & Defense | medium | yfinance |

## Review Notes

- financial_compare packet: `agents/runs/2026-05-16_weekly/evidence_packets/2026-05-16_financial_compare_company_avav.json`
- confidence_counts: {"high": 3, "low": 1, "medium": 11}
- status_counts: {"conflict": 1, "consistent": 14}
- single_provider_metrics: company_name, fifty_two_week_high, fifty_two_week_low, industry, pe_ratio, previous_high, previous_low, previous_open, previous_volume, previous_vwap, sector
- missing_core_metrics: none
- low_confidence_core_metrics: market_cap
- conflicts: 1
- material_conflicts: 1
- taxonomy_conflicts: 0

## Provider Conflicts

- market_cap: material; Relative spread exceeds 3% tolerance.
  - values: {"polygon": 8363500084.17, "yfinance": 7995601218.0}
- recommended_company_file_action: Do not update financial conclusions until conflicts or low-confidence core metrics are reviewed.
