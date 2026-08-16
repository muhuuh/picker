# Sheet Candidate Research Summary: Soitec Correction

Generated: 2026-05-24

Run status: verified for follow-up. This run corrects the previous plain `SOI` ticker collision by researching Soitec S.A. as `SOI.PA` on Euronext Paris.

Primary gate artifact: `agents/runs/2026-05-24_sheet-intake-soitec-soi/market_research/candidate_verification_result.md`

## Routing View

| Ticker | Company | Workflow status | Suggested route before user decision | Why |
| --- | --- | --- | --- | --- |
| SOI.PA | Soitec SA | verified for follow-up | High-interest monitoring candidate, but wait for/inspect the 2026-05-27 annual results and investor-day context before deciding | AI photonics and silicon photonics substrate optionality is real, but the stock has already rerated hard and the current valuation is demanding. |

## Short Note

Soitec is a French engineered semiconductor-substrate company with exposure to RF-SOI, FD-SOI, Photonics-SOI, and SmartSiC. The current investor narrative is centered on AI data-center photonics and potential co-packaged optics demand, not on the legacy mobile/RF cycle alone.

The company-news review found source-backed developments from Soitec and market sources: Q3 FY2026 revenue was EUR 160 million, up 18% sequentially at constant exchange rates and scope but down 29% year over year as reported. Management described the setup as mixed: strong AI demand is offset by automotive weakness and RF-SOI customer inventory correction. Q4 FY2026 revenue was guided to grow around 20% sequentially at constant exchange rates and scope.

The valuation snapshot is now cleanly tied to `SOI.PA`: market cap about EUR 6.33 billion, trailing P/E about 633x, forward P/E about 506x, P/S about 8.08x, TTM revenue about EUR 784 million, and EV/EBITDA about 29.4x. These are single-provider yfinance metrics, so they are usable for sheet context but should be cross-checked before a buy/sell decision.

The strongest positive signal is the Morgan Stanley photonics reset reported by MarketScreener: target price raised to EUR 200 from EUR 70, with silicon photonics revenue estimates revised upward for 2028. The main negative signal is that the stock has already rerated sharply while profitability remains thin and a large part of the business still depends on mobile, automotive, and inventory-cycle recovery.

Evidence: `reports/company_news_specialist/SOI.PA_company_news_review.md`, `reports/financial_data_specialist/SOI.PA_financial_review.md`, `raw/yfinance/SOI.PA_snapshot.json`

## Sheet Update Recommendation

- Processing status: `done`
- Ticker: `SOI.PA`
- Name: `Soitec SA`
- Industry: `Semiconductor materials / engineered substrates`
- Mcap: `EUR 6.33B`
- Forward PE: `506.1`
- P/S: `8.08`
- Forecast: `Q4 FY26 revenue guided ~20% sequential; MS target EUR200 from EUR70 on AI photonics`
- Comment: `Corrected from conflicted SOI to SOI.PA. AI photonics upside is strong, but valuation is demanding after sharp rerating; review 2026-05-27 annual results before monitor/reject decision.`
