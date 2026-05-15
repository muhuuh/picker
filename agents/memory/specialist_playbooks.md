# Specialist Playbooks

Last updated: 2026-05-10

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
- Deterministic commands: `python -m stock_research news contents-follow-up --ticker TICKER --run-id RUN_ID`, then `python -m stock_research news review --ticker TICKER --run-id RUN_ID`.
- Use for: latest company developments, product/customer/regulatory/news impacts, and source discovery.
- Output: evidence packet with claims, risks, contradictions, unknowns, and recommended updates.
- Gotcha: search highlights/headlines are routing evidence only. Keep the review `partial_review` until Exa contents extraction succeeds for selected URLs. Do not use news articles as final proof for financial metrics when market-data providers or filings are available.

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
- SDK status: `discovery_specialist` is implemented for market-research fanout and should combine Exa-verified leads with Grok/X social-signal leads.

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
- SDK status: `grok_discovery_specialist` is implemented for market-research fanout and should explicitly surface niche trends, hype, rumors, credible X posts/accounts, and verification tasks.

## Exa Industry Research Specialist

- Primary tools: Exa `industry`, Exa `general`, Exa `news`, Exa `company`, and Exa `contents`.
- Use for: source-backed industry context, public-company discovery, supplier/customer ecosystems, and verification of Grok/X leads.
- Output: industry/theme specialist result with sources, candidate leads, contradictions, and follow-up contents tasks.
- Gotcha: Exa snippets are not enough for material claims; use contents extraction or primary sources for high-impact updates.
- SDK status: `exa_industry_specialist` is implemented for market-research fanout.

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
- SDK proposal updates must use `python -m stock_research agent-runtime apply-proposal --run-id RUN_ID --proposal-id ORP-0001 --write`; do not let a writer specialist bypass the approved-proposal gate.

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

- id: memory-2026-05-04-company-news-specialist-review-is-implemented
- date: 2026-05-04
- type: procedural
- scope: news
- status: active
- confidence: high
- trigger/source: deterministic company news specialist implementation
- lesson: Company-news specialist review is implemented through python -m stock_research news contents-follow-up --ticker TICKER --run-id RUN_ID followed by python -m stock_research news review --ticker TICKER --run-id RUN_ID. It consumes Exa company-news packets plus contents packets, emits specialist evidence plus raw and markdown review artifacts, and keeps search-highlight-only results as partial reviews.
- use_when: Running company news specialist work, building company research orchestration, or preparing company-file developments/news update proposals.
- do_not_use_when: Financial-data review, X/social sentiment review, or making investment thesis changes from headlines alone.
- evidence: stock_research/company_news_specialist.py, docs/descriptions/company_news_specialist.md, tests/test_company_news_specialist.py
- owner: company news specialist
- next_review: 2026-06-01

- id: memory-2026-05-10-sdk-financial-specialist-uses-deterministic-financial-artifacts
- date: 2026-05-10
- type: procedural
- scope: financial
- status: active
- confidence: high
- trigger/source: SDK financial specialist implementation
- lesson: The SDK financial specialist is a synthesis layer over existing deterministic financial_compare and financial_data_specialist artifacts. It is registered as financial_specialist, exposed as an agent tool, and included in company-research fanout. It must not replace financial_compare or treat Exa/Grok as financial metric providers.
- use_when: Building company-research fanout, financial specialist prompts, main orchestrator financial review tools, or tests around SDK specialist composition.
- do_not_use_when: Planning raw market-data provider execution, bypassing deterministic financial comparison, or using social/news sources as financial metric evidence.
- evidence: stock_research/agent_runtime/specialists/financial.py, agents/specialists/prompts/financial.md, agents/specialists/specs/financial.md, tests/test_agent_runtime.py
- owner: financial specialist
- next_review: 2026-06-10

- id: memory-2026-05-10-sdk-sentiment-specialist-uses-grok-social-signal
- date: 2026-05-10
- type: procedural
- scope: sentiment
- status: active
- confidence: high
- trigger/source: SDK xAI/Grok sentiment specialist implementation
- lesson: The SDK sentiment specialist is a synthesis layer over existing xAI/Grok x_search artifacts. It is registered as sentiment_specialist, exposed as an agent tool, and included in company-research fanout. It must not call direct X.com APIs or treat social output as verified fact.
- use_when: Building sentiment specialist prompts, company-research fanout, social-signal alerts, or tests around Grok/X sentiment handling.
- do_not_use_when: Verifying factual claims, updating financial metrics, or bypassing Exa/SEC/financial-provider verification for material claims found in social discussion.
- evidence: stock_research/agent_runtime/specialists/sentiment.py, agents/specialists/prompts/sentiment.md, agents/specialists/specs/sentiment.md, stock_research/memory.py, tests/test_agent_runtime.py
- owner: xAI Grok sentiment specialist
- next_review: 2026-06-10

- id: memory-2026-05-10-sdk-filing-specialist-uses-sec-artifacts
- date: 2026-05-10
- type: procedural
- scope: provider
- status: active
- confidence: high
- trigger/source: SDK SEC filing specialist implementation
- lesson: The SDK filing specialist is a synthesis layer over existing SEC EDGAR artifacts. It is registered as filing_specialist, exposed as an agent tool, and included in company-research fanout. It must not assume European filing coverage from SEC.
- use_when: Building filing specialist prompts, company-research fanout, SEC filing review, or tests around filing evidence handling.
- do_not_use_when: Researching non-U.S. filings without a separate provider, bypassing SEC User-Agent requirements, or updating company files without source-backed proposals.
- evidence: stock_research/agent_runtime/specialists/filing.py, agents/specialists/prompts/filing.md, agents/specialists/specs/filing.md, tests/test_agent_runtime.py
- owner: SEC filing specialist
- next_review: 2026-06-10

- id: memory-2026-05-10-sdk-company-search-specialist-is-stock-agnostic
- date: 2026-05-10
- type: procedural
- scope: news
- status: active
- confidence: high
- trigger/source: SDK Exa company-search specialist and manifest company-search planning implementation
- lesson: The SDK company-search specialist is stock-agnostic. It is registered as company_search_specialist, runs from a ticker parameter, and synthesizes existing Exa company/general search artifacts. Per-run task ids like company_search_aapl are labels for one ticker run, not ticker-specific agent implementations.
- use_when: Building company-research fanout, Exa company search prompts, tracked-ticker manifests, or human stock-research routing.
- do_not_use_when: Treating Exa search snippets as final proof, creating one-off ticker-specific agent modules, or bypassing Exa contents follow-up for material claims.
- evidence: stock_research/agent_runtime/specialists/company_search.py, agents/specialists/prompts/company_search.md, agents/specialists/specs/company_search.md, stock_research/manifest.py, tests/test_agent_runtime.py, tests/test_stock_research_core.py
- owner: Exa company-search specialist
- next_review: 2026-06-10

- id: memory-2026-05-10-sdk-risk-thesis-writer-quality-lanes
- date: 2026-05-10
- type: procedural
- scope: global
- status: active
- confidence: high
- trigger/source: Added remaining SDK company-research specialist lanes.
- lesson: Risk/thesis, writer, and quality-review SDK specialists are generic synthesis lanes in company-research fanout. The writer lane should draft proposal-ready updates only; deterministic proposal review and approved-proposal writer gates still control actual company-file edits.
- use_when: Building company-research fanout, interpreting scheduled company-research artifacts, or extending writer/quality specialists.
- do_not_use_when: Applying unapproved file writes, bypassing human review, or treating quality-review output as an automatic trade decision.
- evidence: stock_research/agent_runtime/specialists/risk_thesis.py, stock_research/agent_runtime/specialists/writer.py, stock_research/agent_runtime/specialists/quality_review.py, agents/specialists/prompts/risk_thesis.md, agents/specialists/prompts/writer.md, agents/specialists/prompts/quality_review.md, tests/test_agent_runtime.py
- owner: company research specialists
- next_review: 2026-06-10

- id: memory-2026-05-10-discovery-candidate-lead-schema
- date: 2026-05-10
- type: procedural
- scope: specialist
- status: active
- confidence: high
- trigger/source: Manual market-research runner now extracts and gates typed discovery candidates.
- lesson: Discovery specialists should output candidate leads with ticker/company, source channels, source ids, verification status, hype level, rumor flag, rejected cooldown status, and next action. Grok-only leads are verification tasks; Exa/Grok overlap can move to human review, not automatic monitoring.
- use_when: Building discovery prompts, reviewing market-research reports, adding discovery quality gates, or deciding how to classify candidate leads from Exa and Grok.
- do_not_use_when: Updating company facts, making direct trade recommendations, or promoting candidates without source ids and non-social verification.
- evidence: stock_research/agent_runtime/outputs.py, stock_research/market_research_runner.py, tests/test_market_research_runner.py
- owner: discovery specialist
- next_review: 2026-06-10

- id: memory-2026-05-14-real-source-ids-in-specialist-proposals
- date: 2026-05-14
- type: procedural
- scope: specialist
- status: active
- confidence: high
- trigger/source: Human-facing AMZN reports exposed generic placeholder ids such as financial/company-news packet labels instead of the evidence that supported each claim.
- lesson: Specialist proposals and human-facing reports must cite actual provider source ids or ticker-specific artifact ids. Do not emit generic placeholders such as `financial_compare_packet`, `company_news_packet`, `exa_news_packet`, `company_news_specialist_report`, or `financial_specialist_report` as evidence for a claim.
- use_when: Writing company-news, financial, risk/thesis, opportunity, writer, quality-review, or final-digest outputs.
- do_not_use_when: Naming an internal artifact purely as an input packet in an audit section; even then, prefer ticker-specific ids or artifact paths.
- evidence: `stock_research/company_news_specialist.py`, `stock_research/financial_specialist.py`, `agents/specialists/prompts/risk_thesis.md`, `tests/test_company_news_specialist.py`, `tests/test_financial_specialist.py`
- owner: specialist writers
- next_review: 2026-06-15

- id: memory-2026-05-16-company-file-factual-writer-formatting
- date: 2026-05-16
- type: procedural
- scope: writer
- status: active
- confidence: high
- trigger/source: First AMZN factual company-file sync exposed raw dictionary rendering in human-facing rows.
- lesson: The scoped company-file factual updater may auto-apply low-risk opportunity-assessment summaries, but it must render structured evidence as clean investor text, not raw JSON/Python dictionaries. Extract fields such as claim, summary, title, or development; format percent-like financial values as percentages; write only automated factual/source/change-log sections; keep thesis/status/trade changes approval-gated.
- use_when: Building or changing company-file writers, opportunity-assessment summaries, weekly run-end factual sync, or human-facing FYI update summaries.
- do_not_use_when: Applying thesis/opinion/status/strategy changes, promoting stocks, or editing company files outside the scoped writer/approved-proposal paths.
- evidence: `stock_research/company_file_factual_update.py`, `tests/test_company_file_factual_update.py`, `agents/runs/2026-05-16_weekly/company_file_factual_updates.md`
- owner: company file updater
- next_review: 2026-06-16
