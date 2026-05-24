# Sheet Candidate Research Summary: 2026-05-24

Source: Google Sheet `action=research` rows 7-17.

Run status: partial but usable. Ten candidates completed provider and analysis verification. PENG was skipped because it already exists in monitoring.

Primary gate artifact: `agents/runs/2026-05-24_sheet-intake-new-stocks/market_research/candidate_verification_result.md`

## Routing View

| Ticker | Company / intended company | Workflow status | Suggested route before user decision | Why |
| --- | --- | --- | --- | --- |
| AIXA | AIXTRON SE | needs human review | Fix/refresh exchange-aware financials, then likely monitoring candidate | News evidence points to AIXTRON order-intake recovery and raised 2026 guidance, but provider financials did not resolve the ticker cleanly. |
| AMBQ | Ambiq Micro, Inc. | verified for follow-up | Speculative monitoring candidate | Edge-AI revenue growth is strong, but the company is loss-making and valuation is high at roughly 21x sales. |
| ARM | Arm Holdings plc | needs human review | Lower-priority monitoring candidate unless you want mega-cap AI platform exposure | Excellent AI/platform momentum, but valuation is extreme at roughly 66x sales and 356x earnings. |
| FCEL | FuelCell Energy, Inc. | verified for follow-up | Reject/pass unless you want a very speculative power/datacenter basket item | Revenue growth and AI power narrative are visible, but losses are severe and the business remains execution-heavy. |
| FLNC | Fluence Energy, Inc. | needs human review | Monitoring candidate after resolving market-cap/share-class mismatch | Storage order intake and hyperscaler agreements are interesting; valuation is more reasonable at roughly 1.5x sales, but provider market-cap data conflicted. |
| LSCC | Lattice Semiconductor Corp. | verified for follow-up | Monitoring candidate with valuation warning | Strong low-power FPGA/compute recovery signals, but valuation is very demanding at roughly 34x sales and more than 1000x trailing earnings. |
| MRVL | Marvell Technology, Inc. | verified for follow-up | Monitoring candidate with near-term earnings-event risk | AI ASIC, optical interconnect, and NVIDIA partnership evidence are strong, but the stock already prices in a lot at roughly 21x sales. |
| OCC | Optical Cable Corp. | verified for follow-up | Low-priority niche monitoring candidate | Microcap fiber/cable name with improving gross profit and modest P/S around 1.5x, but profitability is weak and search noise is high. |
| SOI | likely Soitec S.A., but ticker conflicted | needs human review | Fix ticker before any decision | Financial providers matched Solaris Oilfield Infrastructure, while news evidence surfaced Soitec. Treat this row as unresolved until the intended listing is confirmed, likely `SOI.PA` if the target is Soitec. |
| VPG | Vishay Precision Group, Inc. | verified for follow-up | Monitoring candidate after valuation check | Q1 showed revenue growth, bookings above $100 million, and sensor/robotics optionality; valuation is not cheap at roughly 4.7x sales and high trailing P/E. |

## Short Notes

### AIXA

Evidence points to AIXTRON SE, not a US ticker. Company-news reports cite stronger optoelectronics demand, Q1 order intake around EUR 171 million, and raised full-year 2026 guidance. The financial provider pass could not resolve core metrics for plain `AIXA`, so this should not be promoted until the Sheet ticker is made exchange-aware.

Evidence: `reports/company_news_specialist/AIXA_company_news_review.md`, `reports/financial_data_specialist/AIXA_financial_review.md`

### AMBQ

Ambiq is a high-growth but still loss-making edge-AI semiconductor candidate. The Q1 evidence says net sales grew 59.3% year over year, gross margin improved, and Q2 sales guidance is $31.0 million to $32.0 million. Financial data is consistent, but the stock is expensive relative to current revenue and still has negative margins.

Evidence: `reports/company_news_specialist/AMBQ_company_news_review.md`, `reports/financial_data_specialist/AMBQ_financial_review.md`

### ARM

Arm has a strong AI infrastructure and platform narrative. Evidence includes record quarterly/full-year results and more than $2 billion of indicated customer demand for its AGI CPU across FYE27 and FYE28. The concern is valuation: provider data shows roughly $326 billion market cap, about $4.9 billion trailing revenue, and very high trailing P/E.

Evidence: `reports/company_news_specialist/ARM_company_news_review.md`, `reports/financial_data_specialist/ARM_financial_review.md`

### FCEL

FuelCell has a visible data-center power narrative and reported 61% Q1 revenue growth. The issue is financial quality: trailing revenue is modest versus market cap, losses remain large, and the investment case depends heavily on execution and customer conversion. This is not a clean monitoring candidate unless you deliberately want speculative energy-infrastructure exposure.

Evidence: `reports/company_news_specialist/FCEL_company_news_review.md`, `reports/financial_data_specialist/FCEL_financial_review.md`

### FLNC

Fluence has one of the better operational setups in this batch: order intake doubled year to date, backlog reached another record level, and management cited hyperscaler supply agreements. The provider set disagreed materially on market cap, so valuation should be refreshed before promotion. If the market cap resolves near the lower provider values, it becomes more interesting.

Evidence: `reports/company_news_specialist/FLNC_company_news_review.md`, `reports/financial_data_specialist/FLNC_financial_review.md`

### LSCC

Lattice has strong recovery signals: Q1 revenue grew 42% year over year, gross margin was around 69% GAAP and 70% non-GAAP, and operating cash flow/free cash flow were healthy. The problem is price: current trailing valuation is very demanding, so monitoring makes sense only if the thesis is that earnings are at an early-cycle trough.

Evidence: `reports/company_news_specialist/LSCC_company_news_review.md`, `reports/financial_data_specialist/LSCC_financial_review.md`

### MRVL

Marvell is a strong AI-infrastructure candidate. Evidence includes the NVIDIA NVLink Fusion partnership, silicon photonics collaboration, NVIDIA's $2 billion investment, and a near-term earnings catalyst scheduled for 2026-05-27. The main risk is that the stock already reflects much of the AI ASIC/optical optimism.

Evidence: `reports/company_news_specialist/MRVL_company_news_review.md`, `reports/financial_data_specialist/MRVL_financial_review.md`

### OCC

Optical Cable is a microcap fiber/cable idea. The verified evidence shows Q1 net sales up 4.4%, gross profit up 16.1%, and gross margin expansion to 32.7%. It is cheap on P/S, but earnings are still weak and the ticker creates search noise with the Office of the Comptroller of the Currency.

Evidence: `reports/company_news_specialist/OCC_company_news_review.md`, `reports/financial_data_specialist/OCC_financial_review.md`

### SOI

This row is unresolved. The financial data matched Solaris Oilfield Infrastructure, but the company-news evidence matched Soitec S.A. and `SOI.PA`. Do not use the current generated financial review for a Soitec decision. Update the Sheet row with the intended listing before any monitoring/rejection decision.

Evidence: `reports/company_news_specialist/SOI_company_news_review.md`, `reports/financial_data_specialist/SOI_financial_review.md`

### VPG

VPG looks like a reasonable small/mid-cap industrial sensing candidate. Q1 revenue grew 17.6%, bookings exceeded $100 million, and management discussed backlog strength plus a higher-growth three-year model. Valuation is not low for the current margin profile, so this needs a valuation check before monitoring.

Evidence: `reports/company_news_specialist/VPG_company_news_review.md`, `reports/financial_data_specialist/VPG_financial_review.md`

## Next Decision Set

- Likely monitor candidates to review first: MRVL, FLNC, VPG, LSCC, AIXA after ticker/financial refresh.
- Speculative monitor candidates: AMBQ, OCC.
- Likely reject/pass unless you want speculative exposure: FCEL.
- Needs Sheet correction before decision: SOI.
- Already monitored: PENG.
