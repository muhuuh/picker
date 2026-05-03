# Stock Tracking CSV Schema

Last updated: 2026-04-30

## Shared Columns

- `ticker`: stock ticker or exchange-specific ticker.
- `company_name`: official or common company name.
- `exchange`: listing exchange.
- `country`: main listing country.
- `currency`: trading currency.
- `sector`: broad sector.
- `industry`: narrower industry.
- `status`: current_holding, monitoring, or rejected.
- `stock_info_file`: path to the detailed company markdown file, when one exists.
- `source`: source for adding the row.
- `price`: latest known price.
- `market_cap`: latest known market capitalization.
- `pe_ratio`: latest known price/earnings ratio, if meaningful.
- `date_found`: date the stock entered the system.
- `date_last_updated`: date the row was last updated.
- `notes`: short scanning notes only.

## Current Holdings Extra Columns

- `next_review_date`: next planned review date.
- `last_filing_checked`: latest date filings were checked.
- `last_news_checked`: latest date news was checked.
- `last_sentiment_checked`: latest date sentiment was checked.
- `alert_level`: none, low, medium, high, urgent.
- `thesis_status`: intact, improving, weakening, broken, unknown.

## Monitoring Extra Columns

- `next_review_date`: next planned review date.
- `last_filing_checked`: latest date filings were checked.
- `last_news_checked`: latest date news was checked.
- `last_sentiment_checked`: latest date sentiment was checked.
- `alert_level`: none, low, medium, high, urgent.
- `watch_reason`: short reason this company is monitored.
- `target_entry_criteria`: what would make it more actionable.

## Rejected Extra Columns

- `date_rejected`: date the company was rejected.
- `next_eligible_review_date`: `date_rejected` plus 6 weeks unless manually overridden.
- `reject_reason`: short reason for rejection.
- `reconsider_trigger`: what would justify a fresh review later.

## Rules

- CSV files are indexes, not research notebooks.
- Keep deep reasoning in company markdown files and category state files.
- Use ISO dates: `YYYY-MM-DD`.
- Leave unknown values blank rather than guessing.
- Do not store private broker/account data or secrets.
