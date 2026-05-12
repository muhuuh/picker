# Source Quality Memory

Last updated: 2026-05-12

Operational memory about provider reliability, source behavior, and known gotchas.

## Active Provider Lessons

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

## Source Hierarchy Status

- Financial source-of-truth hierarchy is still open.
- Until resolved, preserve provider conflicts through `financial_compare` instead of silently picking one provider.
- Social-sentiment sources can create alerts and questions, but not standalone investment facts.
