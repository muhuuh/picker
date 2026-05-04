# Company News Specialist

Last updated: 2026-05-04

## Purpose

The company-news specialist turns an Exa company-news packet plus Exa contents follow-up into a concise review artifact for later orchestrator synthesis and company-file updates.

Implementation: `stock_research/company_news_specialist.py`.

Contents follow-up command:

```powershell
python -m stock_research news contents-follow-up --ticker AAPL --run-id 2026-05-09_weekly
```

Review command:

```powershell
python -m stock_research news review --ticker AAPL --run-id 2026-05-09_weekly
```

Optional explicit Exa news packet:

```powershell
python -m stock_research news review --ticker AAPL --run-id 2026-05-09_weekly --exa-news-packet agents\runs\2026-05-09_weekly\evidence_packets\PACKET.json
```

## Inputs

- Primary input: latest Exa company-news packet for the ticker and run.
- Follow-up input: Exa contents packet for selected high-value URLs.
- The input packet must be a provider-neutral evidence packet from Exa with company subject type.
- `contents-follow-up` makes a live Exa `/contents` call and writes an Exa evidence packet.
- `review` itself is deterministic and does not make live API calls; provider tasks and contents follow-up should run first.

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

- `ready_for_company_update`: source-backed news developments are available and at least one high-value URL has successful Exa contents extraction.
- `partial_review`: no sources were found, unresolved unknowns remain, or only search highlights/headlines exist without contents extraction.
- `needs_human_review`: contradictions exist and should block company-file conclusion updates.

## Workflow Role

```text
Exa company-news packet
  -> Exa contents follow-up for high-value URLs
  -> company_news_specialist review packet/report
  -> company research orchestrator
  -> company-file update specialist
```

Weekly manifests now plan `company_news_contents_follow_up` before `company_news_review` for current holdings, monitoring stocks, and human stock-research requests.

## Guardrails

- Run Exa provider tasks before this specialist.
- Use Exa contents extraction for high-value URLs before marking a company-news review ready for company-file updates.
- Treat this as a news/developments review, not a financial or social-sentiment review.
- Do not update investment conclusions from headlines alone.
- Search highlights are routing evidence. Contents excerpts are the minimum source detail for company-file news/development updates.
