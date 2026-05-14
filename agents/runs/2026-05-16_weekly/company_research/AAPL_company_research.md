# Company Research: AAPL

- run_id: 2026-05-16_weekly
- status: ready
- fanout_status: complete
- stock_bucket: monitoring
- stock_info_file: stock_tracking/stock_info_files/monitoring/AAPL.md

## Summary

Company research packet for AAPL covers 8 evidence packet(s), 4 ready lane(s), 3 partial lane(s), and 0 missing lane(s). Fanout status is complete; review missing lanes before treating this as complete.

## Lanes

- financials: ready (6 packet(s), 1 report(s))
- company_news: partial (0 packet(s), 0 report(s))
  - missing: Run Exa company-news search, contents follow-up, and company_news_review for this ticker.
  - missing: Missing markdown review report for company_news.
- filings: ready (1 packet(s), 0 report(s))
- sentiment: ready (1 packet(s), 0 report(s))
- company_search: partial (0 packet(s), 0 report(s))
  - missing: Run Exa company/general search for this ticker.
- risk_thesis: ready (2 packet(s), 0 report(s))
- opportunity_assessment: partial (0 packet(s), 0 report(s))
  - missing: Run opportunity_assessment after financial, news, filing, sentiment, and company-search evidence is available.

## Specialist Fanout

- financial_aapl: complete via `financial_specialist`
- company_news_aapl: complete via `company_news_specialist`
- company_search_aapl: complete via `company_search_specialist`
- filings_aapl: complete via `filing_specialist`
- sentiment_aapl: complete via `sentiment_specialist`
- risk_thesis_aapl: complete via `risk_thesis_specialist`
- opportunity_aapl: complete via `opportunity_assessment_specialist`
- writer_aapl: complete via `writer_specialist`
- quality_aapl: complete via `quality_reviewer_specialist`

## Next Run Tasks

- None.
