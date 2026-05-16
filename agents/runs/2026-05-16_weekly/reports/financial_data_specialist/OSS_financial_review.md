# Financial Review: OSS

Status: needs_human_review
Reason: Material conflicts or low-confidence core metrics need review before file updates.

## Headline Metrics

| Metric | Value | Confidence | Providers |
| --- | --- | --- | --- |
| company_name | One Stop Systems, Inc. Common Stock | medium | polygon |
| latest_price | 16.47 | high | polygon, yfinance |
| market_cap | 4.27e+08 | low | polygon, yfinance |
| pe_ratio | 149.7 | medium | yfinance |
| currency | usd | high | polygon, yfinance |
| exchange | XNAS | low | polygon, yfinance |
| sector | Technology | medium | yfinance |
| industry | Computer Hardware | medium | yfinance |

## Review Notes

- financial_compare packet: `agents/runs/2026-05-16_weekly/evidence_packets/2026-05-16_financial_compare_company_oss.json`
- confidence_counts: {"high": 2, "low": 2, "medium": 11}
- status_counts: {"conflict": 2, "consistent": 13}
- single_provider_metrics: company_name, fifty_two_week_high, fifty_two_week_low, industry, pe_ratio, previous_high, previous_low, previous_open, previous_volume, previous_vwap, sector
- missing_core_metrics: none
- low_confidence_core_metrics: market_cap, exchange
- conflicts: 2
- material_conflicts: 2
- taxonomy_conflicts: 0

## Provider Conflicts

- exchange: material; Providers disagree after normalization.
  - values: {"polygon": "XNAS", "yfinance": "NCM"}
- market_cap: material; Relative spread exceeds 3% tolerance.
  - values: {"polygon": 427017853.08, "yfinance": 407945692.98246574}
- recommended_company_file_action: Do not update financial conclusions until conflicts or low-confidence core metrics are reviewed.
