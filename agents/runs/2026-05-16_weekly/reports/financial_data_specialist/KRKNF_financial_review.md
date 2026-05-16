# Financial Review: KRKNF

Status: partial_review
Reason: No material numeric conflicts found, but some core metrics are missing or non-thesis metadata/taxonomy labels differ by provider.

## Headline Metrics

| Metric | Value | Confidence | Providers |
| --- | --- | --- | --- |
| latest_price | 5.3 | medium | yfinance |
| market_cap | 1.628e+09 | medium | yfinance |
| pe_ratio | 527 | medium | yfinance |
| currency | USD | medium | yfinance |
| exchange | OQB | medium | yfinance |
| sector | Technology | medium | yfinance |
| industry | Scientific & Technical Instruments | medium | yfinance |

## Review Notes

- financial_compare packet: `agents/runs/2026-05-16_weekly/evidence_packets/2026-05-16_financial_compare_company_krknf.json`
- confidence_counts: {"medium": 9}
- status_counts: {"consistent": 9}
- single_provider_metrics: currency, exchange, fifty_two_week_high, fifty_two_week_low, industry, latest_price, market_cap, pe_ratio, sector
- missing_core_metrics: company_name
- low_confidence_core_metrics: none
- conflicts: 0
- material_conflicts: 0
- taxonomy_conflicts: 0
- metadata_conflicts: 0
- recommended_company_file_action: Update available metrics, but preserve missing-core-metric notes for follow-up.
