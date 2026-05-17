# Financial Data Specialist

Last updated: 2026-05-17

## Purpose

The financial data specialist turns a deterministic `financial_compare` packet into a concise review artifact for later orchestrator synthesis and company-file updates.

Implementation: `stock_research/financial_specialist.py`.

Current command:

```powershell
python -m stock_research financial review --ticker AAPL --run-id 2026-05-09_weekly
```

Optional explicit comparison packet:

```powershell
python -m stock_research financial review --ticker AAPL --run-id 2026-05-09_weekly --financial-compare-packet agents\runs\2026-05-09_weekly\evidence_packets\2026-05-04_financial_compare_company_aapl.json
```

## Inputs

- Primary input: latest `financial_compare` company packet for the ticker and run.
- It does not use Exa or Grok directly.
- It inherits provider conflicts, unknowns, and source references from the comparison packet.

## Outputs

Evidence packet:

```text
agents/runs/{run_id}/evidence_packets/{date}_financial_data_specialist_company_{ticker}.json
```

Raw review JSON:

```text
agents/runs/{run_id}/raw/financial_data_specialist/{TICKER}_financial_review.json
```

Markdown review:

```text
agents/runs/{run_id}/reports/financial_data_specialist/{TICKER}_financial_review.md
```

## Review Statuses

- `ready_for_company_update`: core metrics are present and no material provider conflicts were found.
- `partial_review`: no material conflicts were found, but core metrics are missing.
- `needs_human_review`: provider conflicts, low-confidence core metrics, or valuation sanity warnings remain.

Core metrics:

- company name,
- latest price,
- market cap,
- P/E ratio,
- currency,
- exchange,
- sector,
- industry.

## Workflow Role

```text
financial provider packets
  -> financial_compare packet
  -> financial_data_specialist review packet/report
  -> company research orchestrator
  -> company-file update specialist
```

Weekly manifests now plan `financial_review` analysis tasks after matching `financial_compare` tasks.

## Guardrails

- Do not treat social/news providers as financial comparison inputs.
- Do not hide provider conflicts.
- Single-provider metrics can be useful, but should be marked as lower-confidence context.
- Valuation sanity warnings from `financial_compare` block clean financial conclusions until price, market cap, P/E, and range data are cross-checked through trusted providers or primary/company sources.
- `needs_human_review` means no financial conclusion should be updated automatically.
