# AMBA Report Quality Comparison

Generated: 2026-05-17

## Test Question

Does the human-facing AMBA report improve more from deterministic de-duplication, or from an actual first-principles LLM/Codex synthesis pass over the raw evidence?

## Inputs Read

- Deterministic AMBA opportunity report: `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/AMBA_opportunity_assessment.md`
- Company-news specialist report: `agents/runs/2026-05-16_weekly/reports/company_news_specialist/AMBA_company_news_review.md`
- Financial specialist report: `agents/runs/2026-05-16_weekly/reports/financial_data_specialist/AMBA_financial_review.md`
- Raw Grok/X artifact: `agents/runs/2026-05-16_weekly/raw/xai_grok/xai_x_search_company_amba.json`
- Live Grok web-search artifact: `agents/runs/2026-05-17_amba-report-quality/raw/xai_grok/web_search_company_deep_dive_amba_3a04fb2329.json`
- Attached AMBA Grok PDF, visually inspected through extracted page images from `C:/Users/valen/Downloads/amba_grok_report.pdf`
- Codex synthesis benchmark: `agents/runs/2026-05-17_amba-report-quality/reports/AMBA_codex_synthesis_report.md`

## Result

The better final human report is the Codex synthesis, not the deterministic de-duplicated report.

The deterministic report is better than the earlier stitched version because it no longer repeats the same long claims across many sections. But it still reads like an audit object. It exposes score factors, source lanes, and truncated sub-report structure. That is useful for traceability, not for a reader trying to understand the AMBA opportunity.

The Grok PDF and live Grok web run show the missing shape: a real report starts with what the company does, why the industry setup matters, what X is currently saying, what the numbers imply, what changed recently, then a balanced assessment. The Codex synthesis is strongest because it keeps that readable storyline while also using repo-specific evidence and marking which claims remain unverified.

## Quality Scores

| Output | Human readability | Actionability | Evidence discipline | Main problem | Judgment |
| --- | ---: | ---: | ---: | --- | --- |
| Deterministic AMBA opportunity report | 5/10 | 6/10 | 8/10 | Still audit-shaped and over-compressed; some sections are not useful to a human reader. | Keep as audit/evidence layer, not final report. |
| Attached Grok AMBA PDF / Grok web deep dive | 7/10 | 7/10 | 5/10 | Good story and useful missing numbers, but weaker source verification and no repo/company-file context. | Use as auxiliary raw insight lane. |
| Codex AMBA synthesis benchmark | 8/10 | 8/10 | 7/10 | Needs automated source verification and final-report generation path. | Best candidate for final human-facing report. |

## What The Deterministic Report Still Gets Wrong

- It passes the de-dup gate but remains too mechanical. The executive read says AMBA has "source-backed growth/demand evidence, profitability or cash-conversion evidence, technology or product-positioning evidence," which is technically compact but not a useful investor conclusion.
- It includes audit internals such as score-factor bullets, source coverage state, and "No distinct follow-up beyond the investor insight report above." That belongs in the evidence layer, not the reading layer.
- It has facts without enough interpretation. Example: the report lists Q4 revenue, FY revenue, gross margin, and the May 28 earnings date, but does not clearly frame the next decision as whether Q1 FY2027 proves edge-AI demand broadening into robotics/physical AI while valuation remains defensible.
- It misses context from Grok web/PDF: forward P/E estimate range, consensus target range, cash/debt color, analyst ratings mix, and the "pure-play eyes provider for physical AI" framing.
- It still lets X claims drive too much wording while not converting them into a clean hierarchy of base case, upside watch item, and rumor.

## What Grok Adds To Raw Insights

The live Grok web run and PDF add useful gaps beyond sentiment:

- Business framing: AMBA as low-power edge-AI/computer-vision silicon for local perception, not just a "camera-chip" stock.
- Industry framing: physical AI, robotics, autonomous systems, warehouse automation, ADAS, drones, and security as the relevant demand map.
- Competitive framing: advantage in power efficiency/integrated vision pipeline; disadvantage versus NVIDIA/Qualcomm/Mobileye/Hailo/SiMa scale and ecosystem depth.
- Financial/analyst context: around $3.5B market cap, roughly $81 stock price, trailing P/E not clean because GAAP losses conflict with provider P/E, forward P/E around 100x in the PDF, consensus target around $96 with $80-$115 range, and roughly 18% implied upside.
- News/catalyst framing: May 28, 2026 Q1 FY2027 call as the immediate proof point; FY2026 revenue reacceleration; CV7/developer ecosystem/semi-custom claims as verification targets.

This is more than sentiment. It should become a standard auxiliary company deep-dive lane, with verification before durable thesis updates.

## What Codex Synthesis Adds

The Codex benchmark report reads better because it reorganizes the same evidence around the investor decision:

- Bottom line: AMBA is an active-watch name, but the thesis is proof-needed edge-AI optionality rather than clean fundamentals.
- Investable question: the May 28 call must show whether edge-AI demand is broadening beyond security/auto into robotics or other physical-AI use cases while margins and valuation remain defensible.
- Evidence hierarchy: verified FY2026 revenue/gross-margin facts are separated from Grok web financial/analyst context and from X humanoid speculation.
- Clear bull/bear cases: the bull case needs edge-AI mix, CV7 traction, named design wins, and margin stability; the bear case is that X may be technically right but early by years.
- Actionable next checks: earnings transcript, edge-AI mix, named design wins, analyst/forward valuation verification, peer comparison, and follow-up X evidence.

## Recommendation

Switch the final human-facing opportunity assessment to a Codex/GPT synthesis layer.

The deterministic opportunity assessment should remain in the workflow, but its role should be renamed conceptually to audit/evidence report. The new human synthesis pack should gather the deterministic report, raw Grok/X, Grok web deep dive, company news, financials, filings, and company-file context, then instruct Codex/GPT-5.5 to write the final report from first principles.

The workflow should not rely on de-duplication as the main quality fix. De-duplication is a quality gate. The actual fix is a report-writing layer that reads all evidence, chooses a storyline, keeps only important points, explains why they matter, and labels uncertainty.
