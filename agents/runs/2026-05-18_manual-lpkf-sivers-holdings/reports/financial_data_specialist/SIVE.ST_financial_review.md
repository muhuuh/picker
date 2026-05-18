# Financial Review: SIVE.ST

Status: needs_human_review
Reason: Valuation sanity warnings require cross-provider verification before using headline price, market cap, or P/E conclusions.

## Headline Metrics

| Metric | Value | Confidence | Providers |
| --- | --- | --- | --- |
| company_name | Sivers Semiconductors AB (publ) | medium | fmp |
| latest_price | 55.7 | high | fmp, yfinance |
| market_cap | 1.415e+10 | low | fmp, yfinance |
| pe_ratio | -278.5 | medium | yfinance |
| currency | SEK | high | fmp, yfinance |
| exchange | STO | high | fmp, yfinance |
| sector | Technology | high | fmp, yfinance |
| industry | Semiconductors | high | fmp, yfinance |
| country | SE | medium | fmp |

## Review Notes

- financial_compare packet: `agents/runs/2026-05-18_manual-lpkf-sivers-holdings/evidence_packets/2026-05-18_financial_compare_company_sive_st.json`
- confidence_counts: {"high": 5, "low": 1, "medium": 5}
- status_counts: {"conflict": 1, "consistent": 10}
- single_provider_metrics: company_name, country, fifty_two_week_high, fifty_two_week_low, pe_ratio
- valuation_sanity_warnings: 2
- missing_core_metrics: none
- low_confidence_core_metrics: market_cap
- conflicts: 1
- material_conflicts: 1
- taxonomy_conflicts: 0
- metadata_conflicts: 0

## Provider Conflicts

- market_cap: material; Relative spread exceeds 3% tolerance.
  - values: {"fmp": 14147115001, "yfinance": 16516985856.93806}

## Valuation Sanity Warnings

- 52-week range is unusually wide (21.0x from low to high); check for split, corporate-action, ticker, or stale-data issues before using valuation metrics.
- P/E ratio is single-provider while the valuation snapshot has weak or suspicious coverage; do not treat the multiple as clean consensus.
- recommended_company_file_action: Do not update financial conclusions until conflicts or low-confidence core metrics are reviewed.
