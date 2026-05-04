# Setup

Last updated: 2026-05-04

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
python -m stock_research memory validate
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

xAI Grok requires an API key:

```text
XAI_API_KEY="..."
```

Market-data cross-check providers require keys when used:

```text
FMP_API_KEY="..."
POLYGON_API_KEY="..."
ALPHA_VANTAGE_API_KEY="..."
```

`MASSIVE_API_KEY` is also accepted for Polygon/Massive.

Provider integrations planned later may use:

- Exa,
- xAI/Grok,
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

## FMP

Fetch quote, profile, TTM key metrics, and TTM ratios:

```powershell
python -m stock_research fmp company --ticker AAPL --run-id 2026-05-09_weekly
```

Optional TTM statements:

```powershell
python -m stock_research fmp company --ticker AAPL --run-id 2026-05-09_weekly --include-statements
```

## Polygon / Massive

Fetch U.S. ticker details and previous-day OHLC:

```powershell
python -m stock_research polygon company --ticker AAPL --run-id 2026-05-09_weekly
```

## Alpha Vantage

Fetch Global Quote and Overview:

```powershell
python -m stock_research alpha-vantage company --ticker AAPL --run-id 2026-05-09_weekly
```

Optional statements and earnings:

```powershell
python -m stock_research alpha-vantage company --ticker AAPL --run-id 2026-05-09_weekly --include-statements
```

## Financial Comparison

Compare financial provider packets for one ticker:

```powershell
python -m stock_research financial compare --ticker AAPL --run-id 2026-05-09_weekly
```

This step only compares financial/profile/market-data packets. Exa and xAI/Grok packets are not inputs.

Run the deterministic financial-data specialist review after comparison:

```powershell
python -m stock_research financial review --ticker AAPL --run-id 2026-05-09_weekly
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

## xAI Grok

Research recent X sentiment/news with Grok x_search:

```powershell
python -m stock_research xai x-search --ticker AMD --company-name "Advanced Micro Devices" --subject-type company --subject-id AMD --run-id 2026-05-09_weekly
```

Research an industry/theme:

```powershell
python -m stock_research xai x-search --topic "European grid infrastructure" --research-kind industry_sentiment --subject-type industry --subject-id european_grid_infrastructure --run-id 2026-05-09_weekly
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

Inspect planned provider tasks without making live API calls:

```powershell
python -m stock_research provider-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json
```

Execute planned provider tasks:

```powershell
python -m stock_research provider-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json --execute
```

Run artifacts are intended to be inspectable repo state. Review them before committing if they contain noisy or temporary output.

## Operational Agent Memory

Start with:

```text
agents/memory/memory_index.md
```

The memory files are structured Markdown and require no extra setup. They store operational lessons, source-quality notes, specialist playbooks, evaluation metrics, and deprecated behavior. Do not store secrets, raw provider output, or ordinary company investment facts in `agents/memory/`.

Validate and inspect memory:

```powershell
python -m stock_research memory summary
python -m stock_research memory validate
python -m stock_research memory context --task sentiment
python -m stock_research memory reflect-run --run-id 2026-05-09_weekly --write
python -m stock_research memory recurring-failures --write
python -m stock_research memory finalize-run --run-id 2026-05-09_weekly
```

Add or deprecate structured operational memory:

```powershell
python -m stock_research memory add --type procedural --scope orchestrator --trigger-source "..." --lesson "..." --use-when "..." --do-not-use-when "..." --evidence "..." --owner "..." --next-review 2026-06-01
python -m stock_research memory deprecate --id ITEM_ID --reason "..."
```

Finalize a weekly/manual run after run summary and quality report generation:

```powershell
python -m stock_research memory finalize-run --run-id 2026-05-09_weekly
```

This writes memory reflection artifacts, recurring failure reports, and `finalization.json` / `finalization.md` for the run. It does not apply proposed memory updates automatically.
