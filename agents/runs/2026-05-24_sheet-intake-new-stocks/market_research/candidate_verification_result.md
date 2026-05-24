# Candidate Verification Result: 2026-05-24_sheet-intake-new-stocks

Generated: 2026-05-24
Status: needs_human_review

## Findings

- AIXA: Missing provider evidence: polygon, sec_edgar.
- AIXA: At least one specialist review needs human review.
- ARM: At least one specialist review needs human review.
- FLNC: At least one specialist review needs human review.
- SOI: Missing provider evidence: polygon, sec_edgar.
- SOI: At least one specialist review needs human review.

## Candidate Outcomes

| Review ID | Candidate | Tickers | Decision Kind | Status | Findings | Next Actions |
| --- | --- | --- | --- | --- | --- | --- |
| HRQ-0057 | AIXA | AIXA | verify_before_monitoring | needs_human_review | Missing provider evidence: polygon, sec_edgar.; At least one specialist review needs human review. | Treat missing provider evidence as a coverage gap before promotion.; Review the specialist report findings before any monitoring decision.; Company-news evidence is reviewable and can inform a future company file if the candidate is promoted.; This approval is for verification only; a separate monitoring decision is still required. |
| HRQ-0058 | AMBQ | AMBQ | verify_before_monitoring | verified_for_follow_up | None. | Company-news evidence is reviewable and can inform a future company file if the candidate is promoted.; This approval is for verification only; a separate monitoring decision is still required. |
| HRQ-0059 | ARM | ARM | verify_before_monitoring | needs_human_review | At least one specialist review needs human review. | Review the specialist report findings before any monitoring decision.; Company-news evidence is reviewable and can inform a future company file if the candidate is promoted.; This approval is for verification only; a separate monitoring decision is still required. |
| HRQ-0060 | FCEL | FCEL | verify_before_monitoring | verified_for_follow_up | None. | Company-news evidence is reviewable and can inform a future company file if the candidate is promoted.; This approval is for verification only; a separate monitoring decision is still required. |
| HRQ-0061 | FLNC | FLNC | verify_before_monitoring | needs_human_review | At least one specialist review needs human review. | Review the specialist report findings before any monitoring decision.; Company-news evidence is reviewable and can inform a future company file if the candidate is promoted.; This approval is for verification only; a separate monitoring decision is still required. |
| HRQ-0062 | LSCC | LSCC | verify_before_monitoring | verified_for_follow_up | None. | Company-news evidence is reviewable and can inform a future company file if the candidate is promoted.; This approval is for verification only; a separate monitoring decision is still required. |
| HRQ-0063 | MRVL | MRVL | verify_before_monitoring | verified_for_follow_up | None. | Company-news evidence is reviewable and can inform a future company file if the candidate is promoted.; This approval is for verification only; a separate monitoring decision is still required. |
| HRQ-0064 | OCC | OCC | verify_before_monitoring | verified_for_follow_up | None. | Company-news evidence is reviewable and can inform a future company file if the candidate is promoted.; This approval is for verification only; a separate monitoring decision is still required. |
| HRQ-0065 | SOI | SOI | verify_before_monitoring | needs_human_review | Missing provider evidence: polygon, sec_edgar.; At least one specialist review needs human review. | Treat missing provider evidence as a coverage gap before promotion.; Review the specialist report findings before any monitoring decision.; Company-news evidence is reviewable and can inform a future company file if the candidate is promoted.; This approval is for verification only; a separate monitoring decision is still required. |
| HRQ-0066 | VPG | VPG | verify_before_monitoring | verified_for_follow_up | None. | Company-news evidence is reviewable and can inform a future company file if the candidate is promoted.; This approval is for verification only; a separate monitoring decision is still required. |

## AIXA

### Provider Checks

| Task | Provider | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_yfinance_aixa_hrq_0057 | yfinance | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_yfinance_company_aixa.json |
| candidate_exa_news_aixa_hrq_0057 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_aixa_candidate_exa_news_aixa_hrq_0057.json |
| candidate_exa_company_search_aixa_hrq_0057 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_aixa_candidate_exa_company_search_aixa_hrq_0057.json |
| candidate_xai_x_search_aixa_hrq_0057 | xai_grok | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_xai_grok_company_aixa_candidate_xai_x_search_aixa_hrq_0057.json |
| candidate_fmp_aixa_hrq_0057 | fmp | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_fmp_company_aixa.json |
| candidate_alpha_vantage_aixa_hrq_0057 | alpha_vantage | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_alpha_vantage_company_aixa.json |
| candidate_polygon_aixa_hrq_0057 | polygon | missing | No matching evidence packet found. |
| candidate_sec_aixa_hrq_0057 | sec_edgar | missing | No matching evidence packet found. |

### Analysis Checks

| Task | Tool | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_company_news_contents_follow_up_aixa_hrq_0057 | company_news_contents_follow_up | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_aixa_candidate_company_news_contents_follow_up_aixa_hrq_0057.json |
| candidate_company_news_review_aixa_hrq_0057 | company_news_review | ready_for_company_update | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/company_news_specialist/AIXA_company_news_review.md |
| candidate_financial_compare_aixa_hrq_0057 | financial_compare | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_financial_compare_company_aixa.json |
| candidate_financial_review_aixa_hrq_0057 | financial_review | needs_human_review | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/financial_data_specialist/AIXA_financial_review.md |

## AMBQ

### Provider Checks

| Task | Provider | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_yfinance_ambq_hrq_0058 | yfinance | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_yfinance_company_ambq.json |
| candidate_exa_news_ambq_hrq_0058 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_ambq_candidate_exa_news_ambq_hrq_0058.json |
| candidate_exa_company_search_ambq_hrq_0058 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_ambq_candidate_exa_company_search_ambq_hrq_0058.json |
| candidate_xai_x_search_ambq_hrq_0058 | xai_grok | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_xai_grok_company_ambq_candidate_xai_x_search_ambq_hrq_0058.json |
| candidate_fmp_ambq_hrq_0058 | fmp | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_fmp_company_ambq.json |
| candidate_alpha_vantage_ambq_hrq_0058 | alpha_vantage | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_alpha_vantage_company_ambq.json |
| candidate_polygon_ambq_hrq_0058 | polygon | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_polygon_company_ambq.json |
| candidate_sec_ambq_hrq_0058 | sec_edgar | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_sec_edgar_company_ambq.json |

### Analysis Checks

| Task | Tool | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_company_news_contents_follow_up_ambq_hrq_0058 | company_news_contents_follow_up | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_ambq_candidate_company_news_contents_follow_up_ambq_hrq_0058.json |
| candidate_company_news_review_ambq_hrq_0058 | company_news_review | ready_for_company_update | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/company_news_specialist/AMBQ_company_news_review.md |
| candidate_financial_compare_ambq_hrq_0058 | financial_compare | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_financial_compare_company_ambq.json |
| candidate_financial_review_ambq_hrq_0058 | financial_review | ready_for_company_update | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/financial_data_specialist/AMBQ_financial_review.md |

## ARM

### Provider Checks

| Task | Provider | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_yfinance_arm_hrq_0059 | yfinance | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_yfinance_company_arm.json |
| candidate_exa_news_arm_hrq_0059 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_arm_candidate_exa_news_arm_hrq_0059.json |
| candidate_exa_company_search_arm_hrq_0059 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_arm_candidate_exa_company_search_arm_hrq_0059.json |
| candidate_xai_x_search_arm_hrq_0059 | xai_grok | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_xai_grok_company_arm_candidate_xai_x_search_arm_hrq_0059.json |
| candidate_fmp_arm_hrq_0059 | fmp | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_fmp_company_arm.json |
| candidate_alpha_vantage_arm_hrq_0059 | alpha_vantage | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_alpha_vantage_company_arm.json |
| candidate_polygon_arm_hrq_0059 | polygon | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_polygon_company_arm.json |
| candidate_sec_arm_hrq_0059 | sec_edgar | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_sec_edgar_company_arm.json |

### Analysis Checks

| Task | Tool | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_company_news_contents_follow_up_arm_hrq_0059 | company_news_contents_follow_up | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_arm_candidate_company_news_contents_follow_up_arm_hrq_0059.json |
| candidate_company_news_review_arm_hrq_0059 | company_news_review | ready_for_company_update | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/company_news_specialist/ARM_company_news_review.md |
| candidate_financial_compare_arm_hrq_0059 | financial_compare | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_financial_compare_company_arm.json |
| candidate_financial_review_arm_hrq_0059 | financial_review | needs_human_review | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/financial_data_specialist/ARM_financial_review.md |

## FCEL

### Provider Checks

| Task | Provider | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_yfinance_fcel_hrq_0060 | yfinance | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_yfinance_company_fcel.json |
| candidate_exa_news_fcel_hrq_0060 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_fcel_candidate_exa_news_fcel_hrq_0060.json |
| candidate_exa_company_search_fcel_hrq_0060 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_fcel_candidate_exa_company_search_fcel_hrq_0060.json |
| candidate_xai_x_search_fcel_hrq_0060 | xai_grok | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_xai_grok_company_fcel_candidate_xai_x_search_fcel_hrq_0060.json |
| candidate_fmp_fcel_hrq_0060 | fmp | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_fmp_company_fcel.json |
| candidate_alpha_vantage_fcel_hrq_0060 | alpha_vantage | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_alpha_vantage_company_fcel.json |
| candidate_polygon_fcel_hrq_0060 | polygon | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_polygon_company_fcel.json |
| candidate_sec_fcel_hrq_0060 | sec_edgar | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_sec_edgar_company_fcel.json |

### Analysis Checks

| Task | Tool | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_company_news_contents_follow_up_fcel_hrq_0060 | company_news_contents_follow_up | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_fcel_candidate_company_news_contents_follow_up_fcel_hrq_0060.json |
| candidate_company_news_review_fcel_hrq_0060 | company_news_review | ready_for_company_update | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/company_news_specialist/FCEL_company_news_review.md |
| candidate_financial_compare_fcel_hrq_0060 | financial_compare | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_financial_compare_company_fcel.json |
| candidate_financial_review_fcel_hrq_0060 | financial_review | partial_review | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/financial_data_specialist/FCEL_financial_review.md |

## FLNC

### Provider Checks

| Task | Provider | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_yfinance_flnc_hrq_0061 | yfinance | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_yfinance_company_flnc.json |
| candidate_exa_news_flnc_hrq_0061 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_flnc_candidate_exa_news_flnc_hrq_0061.json |
| candidate_exa_company_search_flnc_hrq_0061 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_flnc_candidate_exa_company_search_flnc_hrq_0061.json |
| candidate_xai_x_search_flnc_hrq_0061 | xai_grok | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_xai_grok_company_flnc_candidate_xai_x_search_flnc_hrq_0061.json |
| candidate_fmp_flnc_hrq_0061 | fmp | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_fmp_company_flnc.json |
| candidate_alpha_vantage_flnc_hrq_0061 | alpha_vantage | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_alpha_vantage_company_flnc.json |
| candidate_polygon_flnc_hrq_0061 | polygon | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_polygon_company_flnc.json |
| candidate_sec_flnc_hrq_0061 | sec_edgar | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_sec_edgar_company_flnc.json |

### Analysis Checks

| Task | Tool | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_company_news_contents_follow_up_flnc_hrq_0061 | company_news_contents_follow_up | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_flnc_candidate_company_news_contents_follow_up_flnc_hrq_0061.json |
| candidate_company_news_review_flnc_hrq_0061 | company_news_review | ready_for_company_update | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/company_news_specialist/FLNC_company_news_review.md |
| candidate_financial_compare_flnc_hrq_0061 | financial_compare | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_financial_compare_company_flnc.json |
| candidate_financial_review_flnc_hrq_0061 | financial_review | needs_human_review | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/financial_data_specialist/FLNC_financial_review.md |

## LSCC

### Provider Checks

| Task | Provider | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_yfinance_lscc_hrq_0062 | yfinance | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_yfinance_company_lscc.json |
| candidate_exa_news_lscc_hrq_0062 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_lscc_candidate_exa_news_lscc_hrq_0062.json |
| candidate_exa_company_search_lscc_hrq_0062 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_lscc_candidate_exa_company_search_lscc_hrq_0062.json |
| candidate_xai_x_search_lscc_hrq_0062 | xai_grok | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_xai_grok_company_lscc_candidate_xai_x_search_lscc_hrq_0062.json |
| candidate_fmp_lscc_hrq_0062 | fmp | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_fmp_company_lscc.json |
| candidate_alpha_vantage_lscc_hrq_0062 | alpha_vantage | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_alpha_vantage_company_lscc.json |
| candidate_polygon_lscc_hrq_0062 | polygon | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_polygon_company_lscc.json |
| candidate_sec_lscc_hrq_0062 | sec_edgar | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_sec_edgar_company_lscc.json |

### Analysis Checks

| Task | Tool | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_company_news_contents_follow_up_lscc_hrq_0062 | company_news_contents_follow_up | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_lscc_candidate_company_news_contents_follow_up_lscc_hrq_0062.json |
| candidate_company_news_review_lscc_hrq_0062 | company_news_review | ready_for_company_update | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/company_news_specialist/LSCC_company_news_review.md |
| candidate_financial_compare_lscc_hrq_0062 | financial_compare | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_financial_compare_company_lscc.json |
| candidate_financial_review_lscc_hrq_0062 | financial_review | partial_review | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/financial_data_specialist/LSCC_financial_review.md |

## MRVL

### Provider Checks

| Task | Provider | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_yfinance_mrvl_hrq_0063 | yfinance | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_yfinance_company_mrvl.json |
| candidate_exa_news_mrvl_hrq_0063 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_mrvl_candidate_exa_news_mrvl_hrq_0063.json |
| candidate_exa_company_search_mrvl_hrq_0063 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_mrvl_candidate_exa_company_search_mrvl_hrq_0063.json |
| candidate_xai_x_search_mrvl_hrq_0063 | xai_grok | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_xai_grok_company_mrvl_candidate_xai_x_search_mrvl_hrq_0063.json |
| candidate_fmp_mrvl_hrq_0063 | fmp | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_fmp_company_mrvl.json |
| candidate_alpha_vantage_mrvl_hrq_0063 | alpha_vantage | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_alpha_vantage_company_mrvl.json |
| candidate_polygon_mrvl_hrq_0063 | polygon | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_polygon_company_mrvl.json |
| candidate_sec_mrvl_hrq_0063 | sec_edgar | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_sec_edgar_company_mrvl.json |

### Analysis Checks

| Task | Tool | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_company_news_contents_follow_up_mrvl_hrq_0063 | company_news_contents_follow_up | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_mrvl_candidate_company_news_contents_follow_up_mrvl_hrq_0063.json |
| candidate_company_news_review_mrvl_hrq_0063 | company_news_review | ready_for_company_update | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/company_news_specialist/MRVL_company_news_review.md |
| candidate_financial_compare_mrvl_hrq_0063 | financial_compare | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_financial_compare_company_mrvl.json |
| candidate_financial_review_mrvl_hrq_0063 | financial_review | partial_review | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/financial_data_specialist/MRVL_financial_review.md |

## OCC

### Provider Checks

| Task | Provider | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_yfinance_occ_hrq_0064 | yfinance | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_yfinance_company_occ.json |
| candidate_exa_news_occ_hrq_0064 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_occ_candidate_exa_news_occ_hrq_0064.json |
| candidate_exa_company_search_occ_hrq_0064 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_occ_candidate_exa_company_search_occ_hrq_0064.json |
| candidate_xai_x_search_occ_hrq_0064 | xai_grok | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_xai_grok_company_occ_candidate_xai_x_search_occ_hrq_0064.json |
| candidate_fmp_occ_hrq_0064 | fmp | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_fmp_company_occ.json |
| candidate_alpha_vantage_occ_hrq_0064 | alpha_vantage | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_alpha_vantage_company_occ.json |
| candidate_polygon_occ_hrq_0064 | polygon | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_polygon_company_occ.json |
| candidate_sec_occ_hrq_0064 | sec_edgar | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_sec_edgar_company_occ.json |

### Analysis Checks

| Task | Tool | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_company_news_contents_follow_up_occ_hrq_0064 | company_news_contents_follow_up | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_occ_candidate_company_news_contents_follow_up_occ_hrq_0064.json |
| candidate_company_news_review_occ_hrq_0064 | company_news_review | ready_for_company_update | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/company_news_specialist/OCC_company_news_review.md |
| candidate_financial_compare_occ_hrq_0064 | financial_compare | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_financial_compare_company_occ.json |
| candidate_financial_review_occ_hrq_0064 | financial_review | partial_review | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/financial_data_specialist/OCC_financial_review.md |

## SOI

### Provider Checks

| Task | Provider | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_yfinance_soi_hrq_0065 | yfinance | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_yfinance_company_soi.json |
| candidate_exa_news_soi_hrq_0065 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_soi_candidate_exa_news_soi_hrq_0065.json |
| candidate_exa_company_search_soi_hrq_0065 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_soi_candidate_exa_company_search_soi_hrq_0065.json |
| candidate_xai_x_search_soi_hrq_0065 | xai_grok | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_xai_grok_company_soi_candidate_xai_x_search_soi_hrq_0065.json |
| candidate_fmp_soi_hrq_0065 | fmp | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_fmp_company_soi.json |
| candidate_alpha_vantage_soi_hrq_0065 | alpha_vantage | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_alpha_vantage_company_soi.json |
| candidate_polygon_soi_hrq_0065 | polygon | missing | No matching evidence packet found. |
| candidate_sec_soi_hrq_0065 | sec_edgar | missing | No matching evidence packet found. |

### Analysis Checks

| Task | Tool | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_company_news_contents_follow_up_soi_hrq_0065 | company_news_contents_follow_up | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_soi_candidate_company_news_contents_follow_up_soi_hrq_0065.json |
| candidate_company_news_review_soi_hrq_0065 | company_news_review | ready_for_company_update | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/company_news_specialist/SOI_company_news_review.md |
| candidate_financial_compare_soi_hrq_0065 | financial_compare | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_financial_compare_company_soi.json |
| candidate_financial_review_soi_hrq_0065 | financial_review | needs_human_review | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/financial_data_specialist/SOI_financial_review.md |

## VPG

### Provider Checks

| Task | Provider | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_yfinance_vpg_hrq_0066 | yfinance | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_yfinance_company_vpg.json |
| candidate_exa_news_vpg_hrq_0066 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_vpg_candidate_exa_news_vpg_hrq_0066.json |
| candidate_exa_company_search_vpg_hrq_0066 | exa | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_vpg_candidate_exa_company_search_vpg_hrq_0066.json |
| candidate_xai_x_search_vpg_hrq_0066 | xai_grok | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_xai_grok_company_vpg_candidate_xai_x_search_vpg_hrq_0066.json |
| candidate_fmp_vpg_hrq_0066 | fmp | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_fmp_company_vpg.json |
| candidate_alpha_vantage_vpg_hrq_0066 | alpha_vantage | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_alpha_vantage_company_vpg.json |
| candidate_polygon_vpg_hrq_0066 | polygon | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_polygon_company_vpg.json |
| candidate_sec_vpg_hrq_0066 | sec_edgar | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_sec_edgar_company_vpg.json |

### Analysis Checks

| Task | Tool | Status | Artifact / Detail |
| --- | --- | --- | --- |
| candidate_company_news_contents_follow_up_vpg_hrq_0066 | company_news_contents_follow_up | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_exa_company_vpg_candidate_company_news_contents_follow_up_vpg_hrq_0066.json |
| candidate_company_news_review_vpg_hrq_0066 | company_news_review | ready_for_company_update | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/company_news_specialist/VPG_company_news_review.md |
| candidate_financial_compare_vpg_hrq_0066 | financial_compare | complete | agents/runs/2026-05-24_sheet-intake-new-stocks/evidence_packets/2026-05-24_financial_compare_company_vpg.json |
| candidate_financial_review_vpg_hrq_0066 | financial_review | partial_review | agents/runs/2026-05-24_sheet-intake-new-stocks/reports/financial_data_specialist/VPG_financial_review.md |
