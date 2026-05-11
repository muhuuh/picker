import unittest

from stock_research.opportunity_assessment import validate_opportunity_assessment


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
        "social_snapshot": {
            "status": "available",
            "sentiment": "positive_social_signal",
        },
    }


if __name__ == "__main__":
    unittest.main()
