# Specialist Playbooks

Last updated: 2026-05-04

Procedural memory for future specialist agents. Specialists should produce structured evidence packets or narrowly scoped file updates.

## Global Specialist Rules

- Read `agents/memory/memory_index.md` and task-relevant memory before work.
- Keep the assigned scope narrow.
- Preserve source metadata and links.
- Mark unknowns instead of inventing missing data.
- Label sentiment as sentiment, not fact.
- Surface contradictions instead of smoothing them away.
- Do not write broad repo changes from a research specialist.
- File-writing specialists should edit only their assigned target files and provide a short change summary with confidence.

## Company News Specialist

- Primary tools: Exa `news`, then Exa `contents` for high-value sources.
- Use for: latest company developments, product/customer/regulatory/news impacts, and source discovery.
- Output: evidence packet with claims, risks, contradictions, unknowns, and recommended updates.
- Gotcha: do not use news articles as final proof for financial metrics when market-data providers or filings are available.

## Exa Industry Research Specialist

- Primary tools: Exa `industry`, Exa `news`, and Exa `contents`.
- Use Exa `general` when validating broad claims or finding primary sources.
- Output: industry/theme evidence packet with key developments, emerging companies, risks, and candidate ideas.
- Gotcha: discovered companies should become candidates only after strategy fit and rejected-cooldown checks.

## Discovery Specialist

- Primary tools: Exa `company`, Exa `general`, and Grok `x_search` for social discovery signals.
- Use for: finding new candidate stocks linked to strategy priorities, industries, and user requests.
- Output: candidate discovery evidence packet plus suggested monitoring additions for human/orchestrator review.
- Gotcha: Grok-discovered tickers require Exa or financial-provider validation before promotion.

## xAI Grok Stock Sentiment Specialist

- Primary tool: Grok `x_search`.
- Use for: recent X discussion, sentiment, recurring claims, skepticism, hype level, and cited posts/accounts to verify.
- Output: social-sentiment evidence packet.
- Gotcha: never present Grok/X output as verified fact. Verify material claims elsewhere.

## xAI Grok Industry Sentiment Specialist

- Primary tool: Grok `x_search` with industry/theme prompts.
- Use for: industry mood, emerging tickers, narratives, and possible bubbles.
- Output: industry sentiment evidence packet and candidate leads.
- Gotcha: candidate leads are leads only until validated by Exa/company/financial sources.

## Financial Data Specialist

- Primary input: `financial_compare` packets.
- Primary tools: yfinance, FMP, Polygon/Massive, Alpha Vantage, SEC companyfacts when available.
- Deterministic command: `python -m stock_research financial review --ticker TICKER --run-id RUN_ID`.
- Use for: price, valuation, ratios, market cap, revenue/profitability signals, and provider disagreements.
- Output: financial specialist evidence packet, raw review JSON, and markdown review report that cite the reconciliation packet and material conflicts.
- Gotcha: Exa and Grok are not financial comparison inputs.

## SEC Filing Specialist

- Primary tool: SEC EDGAR provider.
- Use for: U.S. 10-K, 10-Q, 8-K, submissions, and companyfacts when applicable.
- Output: filing evidence packet with material changes, risk-factor changes, and follow-up questions.
- Gotcha: European filing coverage needs separate future providers and should not be assumed from SEC.

## Risk And Contradiction Specialist

- Primary inputs: current company file, latest evidence packets, financial comparison output, and source-quality memory.
- Use for: conflicts with current thesis, stale assumptions, missing citations, and contradictory provider values.
- Output: contradiction/risk packet and recommended review items.
- Gotcha: do not resolve conflicts by dropping inconvenient data; preserve conflict and assign follow-up.

## Company File Updater

- Primary inputs: assigned company file, relevant evidence packets, quality notes, and current stock status.
- Use for: surgical updates to one company markdown file.
- Output: edited target file plus change summary.
- Gotcha: avoid broad rewrites. Preserve old thesis context unless evidence clearly supersedes it.

## Category State Updater

- Primary inputs: category CSV, category state file, run summary, alerts, and market context.
- Use for: holdings/monitoring/rejected general state updates.
- Output: edited category state file plus change summary.
- Gotcha: keep detailed company reasoning in company files, not category summaries.

## Quality Reviewer

- Primary inputs: evidence packets, proposed file updates, run summary, `source_quality.md`, and `evaluation_metrics.md`.
- Use for: citations, stale data, provider conflicts, overconfidence, schema validity, and human-review gates.
- Output: quality report, human review queue items, and memory-update proposals.
- Gotcha: quality review happens before final memory updates.

- id: memory-2026-05-04-financial-data-specialist-review-is-implemented
- date: 2026-05-04
- type: procedural
- scope: financial
- status: active
- confidence: high
- trigger/source: deterministic financial data specialist implementation
- lesson: Financial-data specialist review is implemented through python -m stock_research financial review --ticker TICKER --run-id RUN_ID. It must consume a financial_compare packet, preserve provider conflicts, and emit specialist evidence plus raw and markdown review artifacts.
- use_when: Running financial specialist work, building company research orchestration, or preparing company-file financial update proposals.
- do_not_use_when: Using Exa or Grok as direct financial metric inputs, or bypassing financial_compare.
- evidence: stock_research/financial_specialist.py, docs/descriptions/financial_data_specialist.md, tests/test_financial_specialist.py
- owner: financial data specialist
- next_review: 2026-06-01
