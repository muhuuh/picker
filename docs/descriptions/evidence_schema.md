# Evidence Schema

Last updated: 2026-05-04

## Purpose

All provider tools and specialist agents should return the same evidence packet shape. This lets the orchestrator compare SEC filings, Exa search results, X sentiment gathered through xAI/Grok, yfinance/FMP/Polygon/Alpha Vantage market data, macro data, and future sources without parsing provider-specific prose.

Implementation: `stock_research/evidence.py`.

Providers currently using this schema:

- `stock_research/providers/sec_edgar.py`
- `stock_research/providers/exa.py`
- `stock_research/providers/xai_grok.py`
- `stock_research/providers/yfinance_provider.py`
- `stock_research/providers/fmp.py`
- `stock_research/providers/polygon_provider.py`
- `stock_research/providers/alpha_vantage.py`
- `stock_research/financial_compare.py`

## Packet Fields

- `packet_id`: stable file-safe ID.
- `created_at`: ISO timestamp.
- `provider`: source provider or tool name, such as `sec_edgar`, `exa`, `xai_grok`, `yfinance`, `fmp`, `polygon`, `alpha_vantage`, `fred`, `ecb`.
- `subject_type`: `company`, `industry`, `theme`, `macro`, `strategy`, `portfolio`, or `provider_test`.
- `subject_id`: ticker, industry, theme, macro topic, or internal ID.
- `time_window`: source time window covered.
- `sources`: normalized source records.
- `claims`: factual or analytical claims tied to source IDs.
- `risks`: risks tied to source IDs.
- `contradictions`: conflicts with current repo claims.
- `recommended_updates`: target file update recommendations.
- `unknowns`: concrete missing facts.
- `raw_artifact_path`: optional path to raw provider output.
- `notes`: implementation notes.

## Source Fields

- `source_id`
- `provider`
- `source_type`: `filing`, `market_data`, `news`, `web`, `social`, `macro_data`, `transcript`, `internal`, or `other`
- `title`
- `url`
- `publisher`
- `published_at`
- `accessed_at`
- `artifact_path`
- `notes`

## Validation Rules

- Every source needs a unique `source_id`.
- Every claim/risk/contradiction/recommended update should cite known `source_ids`.
- Every source should have either a URL or internal artifact path.
- Social data must stay labeled as `social`; it is sentiment, not fact.
- Missing metrics should be put in `unknowns`, not guessed.

## Storage

Evidence packets are stored as JSON under:

```text
agents/runs/{run_id}/evidence_packets/{packet_id}.json
```

Raw provider output can be stored separately and linked via `raw_artifact_path`.

## CLI

Create a minimal placeholder packet:

```powershell
python -m stock_research evidence new --provider exa --subject-type industry --subject-id "European defense" --run-id 2026-05-09_weekly
```

Validate a packet:

```powershell
python -m stock_research evidence validate agents/runs/2026-05-09_weekly/evidence_packets/PACKET.json
```
