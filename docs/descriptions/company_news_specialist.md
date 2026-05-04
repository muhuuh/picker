# Company News Specialist

Last updated: 2026-05-04

## Purpose

The company-news specialist turns an Exa company-news packet into a concise review artifact for later orchestrator synthesis and company-file updates.

Implementation: `stock_research/company_news_specialist.py`.

Current command:

```powershell
python -m stock_research news review --ticker AAPL --run-id 2026-05-09_weekly
```

Optional explicit Exa news packet:

```powershell
python -m stock_research news review --ticker AAPL --run-id 2026-05-09_weekly --exa-news-packet agents\runs\2026-05-09_weekly\evidence_packets\PACKET.json
```

## Inputs

- Primary input: latest Exa company-news packet for the ticker and run.
- The input packet must be a provider-neutral evidence packet from Exa with company subject type.
- This specialist does not make live Exa API calls; provider tasks should run first.

## Outputs

Evidence packet:

```text
agents/runs/{run_id}/evidence_packets/{date}_company_news_specialist_company_{ticker}.json
```

Raw review JSON:

```text
agents/runs/{run_id}/raw/company_news_specialist/{TICKER}_company_news_review.json
```

Markdown review:

```text
agents/runs/{run_id}/reports/company_news_specialist/{TICKER}_company_news_review.md
```

## Review Statuses

- `ready_for_company_update`: source-backed news developments are available for review.
- `partial_review`: no sources were found, or unresolved unknowns remain.
- `needs_human_review`: contradictions exist and should block company-file conclusion updates.

## Workflow Role

```text
Exa company-news packet
  -> company_news_specialist review packet/report
  -> company research orchestrator
  -> company-file update specialist
```

Weekly manifests now plan `company_news_review` analysis tasks for current holdings, monitoring stocks, and human stock-research requests.

## Guardrails

- Run Exa provider tasks before this specialist.
- Use Exa contents extraction for high-value URLs before making deeper thesis changes.
- Treat this as a news/developments review, not a financial or social-sentiment review.
- Do not update investment conclusions from headlines alone.
