# Stock Info Files

This folder contains detailed per-company markdown files.

## Folders

- `current_holdings/`: detailed files for companies we currently hold.
- `monitoring/`: detailed files for companies we are watching.
- `rejected/`: detailed files for rejected companies when the rejection needs durable explanation.

## Naming Convention

Use:

```text
TICKER_company_name.md
```

Examples:

```text
AAPL_apple.md
ASML_asml_holding.md
```

Keep names lowercase after the ticker, use underscores, and avoid spaces.

## File Template

Use `docs/templates/company_stock_info_template.md` when creating a new company file.

## Rules

- Keep CSV files for scanning and routing.
- Keep detailed evidence, thesis, filings, developments, risks, and source notes in company markdown files.
- Cite source URLs or internal run artifacts for material claims.
- Do not store broker credentials, account data, API keys, or private customer data.
