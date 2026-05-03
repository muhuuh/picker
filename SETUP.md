# Setup

Last updated: 2026-05-03

## Requirements

- Python 3.10 or newer.
- `yfinance` is required for live yfinance market-data snapshots.

Install declared dependencies:

```powershell
python -m pip install -e .
```

## Verify Python

```powershell
python --version
```

## Run From Repo Root

```powershell
cd C:\Users\valen\Documents\Code\stocks
python -m stock_research summary
python -m stock_research validate
python -m unittest discover -s tests
```

## Human Intake Routing

Classify a request without editing files:

```powershell
python -m stock_research classify-request "Research ASML, TSM, AMD, and SAP"
```

Append and route a request into durable repo artifacts:

```powershell
python -m stock_research route-request "Research ASML, TSM, AMD, and SAP" --priority high
```

## Evidence Packets

Create a provider-neutral evidence packet:

```powershell
python -m stock_research evidence new --provider provider_test --subject-type provider_test --subject-id smoke --run-id 2026-05-09_weekly
```

Validate a packet:

```powershell
python -m stock_research evidence validate agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_provider_test_provider_test_smoke.json
```

## Environment Variables

The deterministic core does not require API keys.

SEC EDGAR does not require an API key, but it does require a declared User-Agent:

```text
SEC_USER_AGENT="Stock Research your.email@example.com"
```

Use a real contact email or domain you control.

Exa requires an API key:

```text
EXA_API_KEY="..."
```

Provider integrations planned later may use:

- Exa,
- X.com,
- FMP,
- Polygon,
- Alpha Vantage,
- OpenAI or another agent/model provider.

Keep secrets in `.env` or local environment variables. Do not commit `.env`.

Use `.env.example` as a local template.

## SEC EDGAR

Fetch SEC submissions:

```powershell
python -m stock_research sec company --ticker AAPL --run-id 2026-05-09_weekly
```

Include XBRL company facts:

```powershell
python -m stock_research sec company --ticker AAPL --run-id 2026-05-09_weekly --include-facts
```

## yfinance

Fetch a market-data snapshot:

```powershell
python -m stock_research yfinance company --ticker AAPL --run-id 2026-05-09_weekly
```

## Exa

Run a news/industry/company search:

```powershell
python -m stock_research exa search --mode news --query "semiconductor supply chain disruptions Europe" --subject-type industry --subject-id semiconductors --run-id 2026-05-09_weekly
```

Extract contents from a URL:

```powershell
python -m stock_research exa contents --url https://example.com/article --subject-type company --subject-id AAPL --run-id 2026-05-09_weekly --highlights-query "investment relevance and risks"
```

## Generated Run Artifacts

Weekly manifests can be written with:

```powershell
python -m stock_research manifest --write
```

The default output path is:

```text
agents/runs/YYYY-MM-DD_weekly/manifest.json
```

Run artifacts are intended to be inspectable repo state. Review them before committing if they contain noisy or temporary output.
