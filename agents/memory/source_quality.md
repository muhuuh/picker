# Source Quality Memory

Last updated: 2026-05-24

Operational memory about provider reliability, source behavior, and known gotchas.

## Active Provider Lessons

- id: source-2026-05-24-short-ticker-identity-collisions
- date: 2026-05-24
- type: source_quality
- scope: financial
- status: active
- confidence: high
- trigger/source: Sheet-intake verification run for `SOI` mixed Solaris Oilfield financial evidence with Soitec news evidence.
- lesson: Short or exchange-local tickers can collide across U.S. and non-U.S. listings. Before making candidate decisions, compare company identity across financial providers, Exa company/news results, filings, and the user's intended theme. If financial evidence and news evidence name different companies, mark the row `needs fix` and ask for or infer an exchange-aware ticker such as `.DE` or `.PA` before promotion.
- use_when: Processing Google Sheet stock ideas, European tickers, ambiguous short tickers, and provider results where company names disagree.
- do_not_use_when: Providers consistently identify the same company and exchange.
- evidence: `agents/runs/2026-05-24_sheet-intake-new-stocks/market_research/candidate_research_summary.md`, `agents/runs/2026-05-24_sheet-intake-new-stocks/reports/company_news_specialist/SOI_company_news_review.md`, `agents/runs/2026-05-24_sheet-intake-new-stocks/reports/financial_data_specialist/SOI_financial_review.md`
- owner: financial-data specialist
- next_review: 2026-08-24

- id: source-2026-05-03-sec-user-agent-compression
- date: 2026-05-03
- type: source_quality
- scope: provider
- status: active
- confidence: high
- trigger/source: SEC EDGAR provider implementation and live AAPL smoke test.
- lesson: SEC EDGAR is the official U.S. filings source and needs a declared `User-Agent`. Keep compressed-response handling because SEC JSON responses may arrive compressed.
- use_when: SEC filing tasks, provider runner work, and filing specialists.
- do_not_use_when: Non-U.S. filing coverage; evaluate local sources separately.
- evidence: `stock_research/providers/sec_edgar.py`, `docs/descriptions/sec_edgar_provider.md`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_sec_edgar_company_aapl.json`
- owner: SEC filing specialist
- next_review: 2026-08-01

- id: source-2026-05-03-exa-headers-and-modes
- date: 2026-05-03
- type: source_quality
- scope: news
- status: active
- confidence: high
- trigger/source: Exa provider implementation, live smoke tests, and 2026-05-04 official Exa docs re-review.
- lesson: Exa requests should keep explicit `User-Agent` and `Accept: application/json` headers. Use `type: "auto"` plus highlights by default. Use Exa search modes deliberately: `news` for recent company/industry news on the main search endpoint without a news category, `industry` for sector context, `company` with `category: "company"` for discovery, `general` for broad validation, and `/contents` with top-level highlights/text parameters for high-value result extraction before company-file updates.
- use_when: Exa provider tasks, company news specialist, industry research specialist, discovery specialist, and citation follow-up.
- do_not_use_when: Verified financial metrics or social sentiment; use financial providers or Grok respectively.
- evidence: `stock_research/providers/exa.py`, `docs/descriptions/exa_provider.md`, `docs/descriptions/company_news_specialist.md`, `agents/runs/2026-05-09_weekly/reports/company_news_specialist/AAPL_company_news_review.md`
- owner: Exa specialists
- next_review: 2026-08-01

- id: source-2026-05-03-grok-social-signal
- date: 2026-05-03
- type: source_quality
- scope: sentiment
- status: active
- confidence: high
- trigger/source: User correction and xAI/Grok implementation.
- lesson: Grok `x_search` is for X sentiment, narratives, recent discussion, and discovery signals. Treat outputs as social signal, not verified fact. Verify material factual claims with Exa, SEC, yfinance, FMP, Polygon/Massive, Alpha Vantage, or primary sources before updating conclusions. For investor-facing reports, use the full raw Grok artifact when available because evidence packet claim text may be truncated before later high-value sections such as candidate follow-up and scorecards.
- use_when: Sentiment specialists, market discovery, and tracked-stock social-alert tasks.
- do_not_use_when: Filing, valuation, accounting, or verified factual updates.
- evidence: `docs/descriptions/xai_grok_provider.md`, `stock_research/providers/xai_grok.py`, `stock_research/market_research_runner.py`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_xai_grok_company_amd.json`, `agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/raw/xai_grok/manual_xai_x_search_ai_semiconductor_supply_chain_advanced_packaging.json`
- owner: xAI Grok sentiment specialists
- next_review: 2026-08-01

- id: source-2026-05-03-yfinance-cross-check
- date: 2026-05-03
- type: source_quality
- scope: financial
- status: active
- confidence: medium
- trigger/source: yfinance provider implementation.
- lesson: yfinance is useful for quick first-pass market-data snapshots but should be cross-checked before high-impact conclusions or file updates.
- use_when: Initial snapshots, low-cost checks, and financial compare input collection.
- do_not_use_when: Sole basis for buy/sell/valuation conclusions.
- evidence: `stock_research/providers/yfinance_provider.py`, `docs/descriptions/yfinance_provider.md`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_yfinance_company_aapl.json`
- owner: financial-data specialist
- next_review: 2026-08-01

- id: source-2026-05-16-fmp-subscription-unavailable-packets
- date: 2026-05-16
- type: source_quality
- scope: financial
- status: active
- confidence: high
- trigger/source: First real Codex-supervised weekly run over 10 holdings hit FMP HTTP 402 `Premium Query Parameter` responses.
- lesson: FMP tier/subscription, rate-limit, or credential-style failures should first retry the optional `FMP_API_KEY2` fallback when configured, then be represented as explicit unavailable evidence packets if both keys fail. If only some endpoints fail, preserve usable endpoint data such as `profile` and record endpoint-level unknowns instead of discarding the whole FMP packet. Financial review should treat these as coverage gaps and continue with other providers.
- use_when: FMP provider tasks, scheduled weekly runs, financial compare, and provider-quality reporting.
- do_not_use_when: Suppressing real malformed responses, authentication failures, or schema regressions that need debugging.
- evidence: `stock_research/providers/fmp.py`, `tests/test_fmp_provider.py`, `docs/descriptions/fmp_provider.md`, `agents/runs/2026-05-16_weekly/quality_report.md`
- owner: financial-data specialist
- next_review: 2026-06-16

- id: source-2026-05-04-fmp-ttm-cross-check
- date: 2026-05-04
- type: source_quality
- scope: financial
- status: active
- confidence: medium
- trigger/source: FMP provider implementation and AAPL smoke test.
- lesson: FMP is useful for quote/profile/TTM metrics and ratios. Treat it as a market-data cross-check and preserve provider metadata when metrics conflict.
- use_when: Financial compare, valuation snapshots, and company financial specialist work.
- do_not_use_when: Source-of-truth selection has not been finalized; do not hide conflicts.
- evidence: `stock_research/providers/fmp.py`, `docs/descriptions/fmp_provider.md`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_fmp_company_aapl.json`
- owner: financial-data specialist
- next_review: 2026-08-01

- id: source-2026-05-16-alpha-rate-limit-unavailable-packets
- date: 2026-05-16
- type: source_quality
- scope: financial
- status: active
- confidence: high
- trigger/source: First real Codex-supervised weekly run over 10 holdings hit Alpha Vantage daily rate-limit responses after the first batch.
- lesson: Alpha Vantage rate-limit, premium/unavailable, or credential-style messages should first retry the optional `ALPHA_VANTAGE_API_KEY2` fallback when configured, then be written as explicit unavailable evidence packets if both keys fail. This preserves run completeness while keeping valuation/analyst fields marked lower coverage when Alpha cannot answer.
- use_when: Alpha Vantage provider tasks, scheduled weekly runs, financial compare, and rate-limit planning.
- do_not_use_when: Treating Alpha as complete when the unavailable packet says fields were not retrieved.
- evidence: `stock_research/providers/alpha_vantage.py`, `tests/test_alpha_vantage_provider.py`, `docs/descriptions/alpha_vantage_provider.md`, `agents/runs/2026-05-16_weekly/quality_report.md`
- owner: financial-data specialist
- next_review: 2026-06-16

- id: source-2026-05-04-polygon-massive-us-focus
- date: 2026-05-04
- type: source_quality
- scope: financial
- status: active
- confidence: medium
- trigger/source: Polygon/Massive provider implementation and user clarification.
- lesson: Polygon/Massive is useful for U.S. ticker identity and OHLC cross-checks. Treat default stock usage as U.S.-equity focused unless coverage is verified for a specific non-U.S. ticker.
- use_when: U.S. ticker validation, OHLC checks, and financial compare inputs.
- do_not_use_when: Assuming European equity coverage without verification.
- evidence: `stock_research/providers/polygon_provider.py`, `docs/descriptions/polygon_provider.md`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_polygon_company_aapl.json`
- owner: financial-data specialist
- next_review: 2026-08-01

- id: source-2026-05-04-alpha-rate-limit
- date: 2026-05-04
- type: source_quality
- scope: financial
- status: active
- confidence: high
- trigger/source: Alpha Vantage provider implementation and live smoke test.
- lesson: Alpha Vantage free keys can be tightly rate-limited. Keep default pulls light and preserve request spacing/retry behavior for the 1 request/second message.
- use_when: Alpha Vantage provider tasks, financial compare inputs, and manual provider runs.
- do_not_use_when: High-volume scheduled pulls without explicit rate-limit planning.
- evidence: `stock_research/providers/alpha_vantage.py`, `docs/descriptions/alpha_vantage_provider.md`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_alpha_vantage_company_aapl.json`
- owner: financial-data specialist
- next_review: 2026-08-01

- id: source-2026-05-17-small-cap-valuation-sanity
- date: 2026-05-17
- type: source_quality
- scope: financial
- status: active
- confidence: high
- trigger/source: User follow-up research on AXTI found suspicious price/market-cap/P/E values in the prior opportunity assessment.
- lesson: Small-cap, OTC, foreign, and thinly covered tickers need explicit cross-provider sanity checks before valuation fields are used in human-facing conclusions. If price, market cap, P/E, forward P/E, or analyst target values look inconsistent with ticker identity or company scale, mark valuation as lower-confidence and create a verification task instead of presenting the snapshot as clean.
- use_when: Financial compare, opportunity assessment, weekly digest, company-file factual updates, and smaller/OTC-name research.
- do_not_use_when: Suppressing a confirmed primary-source financial metric; preserve the metric with source and explain why it is trusted.
- evidence: `agents/runs/2026-05-17_followup_user_questions/follow_up_research_report.md`, `stock_tracking/stock_info_files/current_holdings/AXTI.md`
- owner: financial-data specialist
- next_review: 2026-06-17

## Source Hierarchy Status

- Financial source-of-truth hierarchy is still open.
- Until resolved, preserve provider conflicts through `financial_compare` instead of silently picking one provider.
- Social-sentiment sources can create alerts and questions, but not standalone investment facts.

- id: source-2026-05-17-grok-web-auxiliary
- date: 2026-05-17
- type: source_quality
- scope: provider
- status: active
- confidence: medium
- trigger/source: Comparison of user-provided Grok 4.3 PDF reports with repo AMBA/KRKNF artifacts on 2026-05-17
- lesson: Grok web-style deep dives can fill identified business, industry, latest-news, analyst-context, and research-check gaps that X-only sentiment scans do not cover. They should be gap-triggered rather than default per-ticker recurring tasks, and material facts from that lane remain auxiliary until verified through Exa contents, filings, company sources, or financial providers.
- use_when: Planning provider tasks or interpreting xAI Grok web_search company deep-dive artifacts.
- do_not_use_when: Replacing primary financial metrics, filings, or verified company/source-backed facts.
- evidence: stock_research/providers/xai_grok.py; stock_research/manifest.py; docs/descriptions/xai_grok_provider.md; docs/plans/human_report_quality_improvement_plan.md
- owner: provider_runner
- next_review: 2026-11-16

- id: source-2026-05-24-yfinance-extended-valuation-metrics
- date: 2026-05-24
- type: source_quality
- scope: financial
- status: active
- confidence: high
- trigger/source: Soitec SOI.PA Sheet correction showed yfinance raw data had forwardPE and priceToSalesTrailing12Months, but normalized packets did not expose them.
- lesson: For yfinance snapshots, preserve extended valuation/profile fields in the evidence packet when available, including company_name, country, forward_pe, price_to_sales_ttm, revenue_ttm, EV/EBITDA, PEG, price/book, EPS, profit margin, and debt/equity. If a Sheet overview cell is blank after research, check whether the raw provider had a field that the normalizer failed to expose before marking it unavailable.
- use_when: Financial provider extraction, Google Sheet overview backfills, and financial_compare coverage checks.
- do_not_use_when: Treating yfinance as sufficient for high-impact buy/sell decisions without cross-provider or primary-source verification.
- evidence: stock_research/providers/yfinance_provider.py; stock_research/financial_compare.py; agents/runs/2026-05-24_sheet-intake-soitec-soi/reports/financial_data_specialist/SOI.PA_financial_review.md
- owner: financial-data specialist
- next_review: 2026-08-24

- id: source-2026-08-16-grok-46-resolution
- date: 2026-08-16
- type: source_quality
- scope: provider
- status: active
- confidence: high
- trigger/source: 2026-08-16 authenticated xAI model check and live company/industry X Search smokes
- lesson: xAI Grok research should request grok-4.6, validate it against the authenticating key's /v1/models catalog before live execution, and record requested/resolved model, tool, reasoning effort, resolution source, and fallback reason. Never replace a missing X-search lane with generic web search.
- use_when: Planning, executing, or reviewing xAI Grok X Search or Web Search provider tasks.
- do_not_use_when: Selecting OpenAI synthesis models or treating Grok/X claims as verified facts.
- evidence: stock_research/providers/xai_grok.py, stock_research/provider_runner.py, agents/runs/2026-08-16_grok-46-smoke/, docs/descriptions/xai_grok_provider.md
- owner: provider workflow
- next_review: 2026-11-16

- id: source-2026-08-16-full-evidence-display-excerpts
- date: 2026-08-16
- type: source_quality
- scope: evidence
- status: active
- confidence: high
- trigger/source: Hidden truncation audit of Exa and Grok evidence packets and downstream company-news formatting
- lesson: Canonical selected provider evidence and bounded display text are different fields. Preserve the complete selected text in Claim.evidence, generate display excerpts only at real sentence boundaries, and record the raw path/selector. Specialists should inspect bounded packet summaries, then retrieve only the full claims they promote; never turn an ellipsis or clipped word into a period.
- use_when: Building provider adapters, evidence packets, SDK evidence tools, specialist summaries, or final-report source promotion.
- do_not_use_when: Copying entire provider payloads into prompts without selection, or treating Grok social claims as verified facts.
- evidence: stock_research/evidence.py, stock_research/text_excerpt.py, stock_research/providers/exa.py, stock_research/providers/xai_grok.py, stock_research/agent_runtime/tools/repo_tools.py, tests/test_evidence.py, tests/test_exa_provider.py, tests/test_xai_grok_provider.py, tests/test_agent_runtime.py
- owner: provider and evidence workflow
- next_review: 2026-11-16
