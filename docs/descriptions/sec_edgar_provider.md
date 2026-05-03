# SEC EDGAR Provider

Last updated: 2026-05-03

## Purpose

The SEC EDGAR provider is the first live data provider integration. It fetches official SEC company submissions and optional XBRL company facts, then writes provider-neutral evidence packets.

Implementation: `stock_research/providers/sec_edgar.py`.

## Official Sources

- SEC EDGAR API documentation: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- SEC Accessing EDGAR Data guidance: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data

Relevant SEC facts:

- SEC `data.sec.gov` APIs do not require authentication or API keys.
- Company submissions are available at `https://data.sec.gov/submissions/CIK##########.json`.
- Company facts are available at `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json`.
- SEC asks automated clients to declare a `User-Agent` header.

## Configuration

No API key is needed.

Set one of these in local environment variables or `.env`:

```text
SEC_USER_AGENT="Stock Research your.email@example.com"
STOCK_RESEARCH_SEC_USER_AGENT="Stock Research your.email@example.com"
```

Use a real contact email or domain you control.

## CLI

Fetch submissions and write an evidence packet:

```powershell
python -m stock_research sec company --ticker AAPL --run-id 2026-05-09_weekly
```

Fetch submissions plus XBRL company facts:

```powershell
python -m stock_research sec company --ticker AAPL --run-id 2026-05-09_weekly --include-facts
```

Pass a one-off user agent:

```powershell
python -m stock_research sec company --ticker AAPL --run-id 2026-05-09_weekly --user-agent "Stock Research your.email@example.com"
```

## Outputs

Raw SEC JSON:

```text
agents/runs/{run_id}/raw/sec_edgar/{TICKER}_submissions.json
agents/runs/{run_id}/raw/sec_edgar/{TICKER}_companyfacts.json
```

Evidence packet:

```text
agents/runs/{run_id}/evidence_packets/{packet_id}.json
```

## Validation

- 2026-05-03: Live smoke test passed for AAPL with `SEC_USER_AGENT` loaded from `.env`.
- Output packet: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_sec_edgar_company_aapl.json`.
- Raw submissions: `agents/runs/2026-05-09_weekly/raw/sec_edgar/AAPL_submissions.json`.
- Provider fetch helper handles plain, gzip, and deflate response bodies.

## Current Limits

- US SEC filers only.
- Ticker lookup uses the SEC company ticker mapping file.
- Current evidence packet summarizes latest filing forms and metadata; it does not yet parse filing text.
- Company facts retrieval is optional because the JSON can be large.
