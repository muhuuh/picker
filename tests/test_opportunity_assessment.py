import unittest
from pathlib import Path

from stock_research.opportunity_assessment import extract_development_items, format_opportunity_assessment_markdown, validate_opportunity_assessment


class OpportunityAssessmentTests(unittest.TestCase):
    def test_taxonomy_only_conflict_is_not_high_risk(self):
        assessment = base_assessment()
        assessment["financial_snapshot"]["taxonomy_conflict_count"] = 1
        assessment["financial_snapshot"]["material_conflict_count"] = 0
        assessment["risk_level"] = "medium"

        findings = validate_opportunity_assessment(assessment)

        self.assertEqual(findings, [])

    def test_material_missing_sources_are_flagged(self):
        assessment = base_assessment()
        assessment["provider_coverage"] = ["xai_grok"]
        assessment["source_ids"] = []

        findings = validate_opportunity_assessment(assessment)

        self.assertTrue(any("financial-data specialist" in finding for finding in findings))
        self.assertTrue(any("company-news specialist" in finding for finding in findings))
        self.assertTrue(any("no source ids" in finding for finding in findings))

    def test_direct_trade_language_is_flagged(self):
        assessment = base_assessment()
        assessment["recommended_next_action"] = "Buy the stock immediately."

        findings = validate_opportunity_assessment(assessment)

        self.assertTrue(any("direct trade language" in finding for finding in findings))

    def test_missing_investor_usefulness_sections_are_flagged(self):
        assessment = base_assessment()
        assessment["investor_insight_report"]["non_obvious_insights"] = []
        assessment["investor_insight_report"]["valuation_snapshot"] = {}
        assessment["investor_insight_report"]["peer_competition_context"] = {}

        findings = validate_opportunity_assessment(assessment)

        self.assertTrue(any("non-obvious" in finding for finding in findings))
        self.assertTrue(any("usable valuation context" in finding for finding in findings))
        self.assertTrue(any("peer/competition" in finding for finding in findings))

    def test_investor_report_markdown_has_high_bar_sections(self):
        assessment = full_report_assessment()

        markdown = format_opportunity_assessment_markdown(Path("."), "2026-05-16_weekly", assessment)

        self.assertIn("## Investor Insight Report", markdown)
        self.assertIn("### Expert / Community Split From X", markdown)
        self.assertIn("### Non-obvious / under-discussed insights to verify", markdown)
        self.assertIn("### Valuation And Analyst Snapshot", markdown)
        self.assertIn("### Decision Table", markdown)
        self.assertIn("Peer/competition set to check", markdown)
        self.assertIn("Forward P/E", markdown)
        self.assertNotIn("sentiment_label", markdown)
        self.assertNotIn("Extract remaining high-value Exa", markdown)

    def test_valuation_sanity_warnings_are_visible_in_human_report(self):
        assessment = full_report_assessment()
        assessment["financial_snapshot"]["valuation_sanity_warning_count"] = 1
        assessment["financial_snapshot"]["valuation_sanity_warnings"] = [
            "52-week range is unusually wide; check for split, corporate-action, ticker, or stale-data issues before using valuation metrics."
        ]
        assessment["investor_insight_report"]["valuation_snapshot"]["valuation_sanity_warnings"] = list(
            assessment["financial_snapshot"]["valuation_sanity_warnings"]
        )

        markdown = format_opportunity_assessment_markdown(Path("."), "2026-05-16_weekly", assessment)

        self.assertIn("Valuation sanity: needs cross-provider verification", markdown)
        self.assertIn("52-week range is unusually wide", markdown)

    def test_development_extraction_rejects_truncated_markdown_fragments(self):
        evidence = """
## Earnings call
Kraken Robotics delivered record 2025 revenue of CAD 102 million (up [...]
026 ## Kraken Robotics Reports 2025 Financial Results
Kraken announced 2025 revenue of CAD 102 million and gross margin of 62%, with 2026 guidance pointing to continued defense and offshore demand.
"""
        items = extract_development_items(evidence)

        self.assertTrue(any("2025 revenue of CAD 102 million" in item for item in items))
        self.assertFalse(any("026 ##" in item for item in items))
        self.assertFalse(any(item.endswith("(up.") for item in items))


def base_assessment() -> dict:
    return {
        "ticker": "AAPL",
        "summary": "AAPL assessment is interesting with evidence-backed positives and reviewable caveats.",
        "recommended_next_action": "Use this as a reviewable holding update and inspect watch items.",
        "provider_coverage": ["financial_data_specialist", "company_news_specialist", "xai_grok", "sec_edgar"],
        "source_ids": ["financial_specialist_report", "company_news_report"],
        "risk_level": "medium",
        "financial_snapshot": {
            "taxonomy_conflict_count": 0,
            "material_conflict_count": 0,
        },
        "news_snapshot": {
            "status": "ready_for_company_update",
            "material_developments": [{"claim": "AWS demand accelerated and operating margins expanded."}],
        },
        "social_snapshot": {
            "status": "available",
            "sentiment": "positive_social_signal",
            "x_pulse": "X investors are constructive because AWS acceleration supports the AI thesis.",
            "bullish_claims": ["AWS and AI partnerships are the dominant bull narrative."],
            "bearish_claims": ["Valuation is the dominant pushback."],
        },
        "investor_insight_report": {
            "executive_read": "AAPL has a clear investor read.",
            "non_obvious_insights": ["AWS memory-cost pressure is under-discussed and should be verified."],
            "valuation_snapshot": {"forward_pe": 25.0, "analyst_target_price": 250.0},
            "peer_competition_context": {"competitors": ["Microsoft", "Google"]},
        },
    }


def full_report_assessment() -> dict:
    assessment = base_assessment()
    assessment.update(
        {
            "status": "ready_for_human_review",
            "opportunity_view": "interesting",
            "opportunity_score": 82,
            "confidence": "medium",
            "thesis_freshness": "fresh_recent_evidence",
            "positives": ["AWS and AI demand are accelerating."],
            "negatives": ["Valuation is the main debate."],
            "watch_items": ["Verify whether AWS growth offsets valuation risk."],
            "data_quality_notes": [],
            "score_factors": ["+10 source-backed news."],
            "filing_snapshot": {"status": "available", "packet_count": 1, "recent_items": ["10-Q available."]},
            "quality_findings": [],
        }
    )
    assessment["financial_snapshot"].update(
        {
            "status": "ready_for_company_update",
            "latest_price": 100.0,
            "market_cap": 1000000000,
            "pe_ratio": 30.0,
            "forward_pe": 24.0,
            "analyst_target_price": 125.0,
            "analyst_target_implied_upside": 0.25,
            "currency": "USD",
        }
    )
    assessment["social_snapshot"].update(
        {
            "citation_count": 2,
            "rumor_flag": False,
            "notable_accounts": ["@analyst"],
            "hype_noise": "Low noise.",
            "investor_implications": ["Verify AWS growth against filings."],
        }
    )
    assessment["investor_insight_report"].update(
        {
            "company_context": {
                "what_it_does": "Cloud, ads, retail, and AI infrastructure.",
                "sector": "Technology",
                "industry": "Cloud and retail",
                "business_model_notes": ["AWS", "ads", "AI"],
            },
            "thesis_and_trends": {
                "core_thesis": "AWS growth supports the thesis.",
                "what_changed_recently": ["AWS growth accelerated."],
                "tailwinds": ["AI demand."],
                "headwinds": ["Valuation risk."],
                "trend_evolution": ["Fundamental trend improved."],
            },
            "community_and_expert_split": {
                "x_pulse": "X is constructive but valuation-aware.",
                "bullish_camp": ["AWS is accelerating."],
                "skeptical_camp": ["Valuation is rich."],
                "notable_accounts_or_posts": ["@analyst"],
                "hype_noise_assessment": "Low noise.",
            },
            "peer_competition_context": {
                "competitors": ["Microsoft", "Google"],
                "positioning_note": "Compare AWS against Azure and Google Cloud.",
            },
            "decision_table": [
                {
                    "dimension": "Growth / demand",
                    "current_read": "AWS growth is improving.",
                    "evidence": "Exa news",
                    "follow_up": "Verify durability.",
                }
            ],
            "next_research_questions": ["Is AWS growth enough to offset valuation risk?"],
        }
    )
    return assessment


if __name__ == "__main__":
    unittest.main()
