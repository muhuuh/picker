import unittest

from stock_research.report_quality import validate_human_facing_markdown


class ReportQualityGoldenTests(unittest.TestCase):
    def test_high_quality_company_report_passes_human_facing_checks(self):
        markdown = """
# AMZN Opportunity Assessment

## Executive Read

AWS acceleration, Anthropic exposure, and Trainium/Bedrock adoption create a clearer AI-infrastructure thesis, while valuation and capex remain the main debate.

## Expert / Community Split From X

- X pulse: experts are debating whether AWS AI demand is now compounding or whether capex will cap free-cash-flow conversion.
- Bullish: Anthropic/OpenAI workloads, Trainium optimization, and margin mix.
- Bearish: valuation near highs and heavy infrastructure reinvestment.

## Sources

- [AMZN opportunity evidence](agents/runs/2026-05-16_weekly/reports/opportunity_assessment/AMZN_opportunity_assessment.md)
"""
        self.assertEqual(validate_human_facing_markdown(markdown), [])

    def test_flags_truncation_dead_citations_raw_dict_and_status_only_sentiment(self):
        markdown = """
# Bad Report

## News

Narrative is gaining ste...
Grok/X social signal: mixed_social_signal
Raw item: {'claim': 'AWS grew', 'confidence': 'medium'}
Source: [xai_x_source_1]
Another dead marker [1]

## News

Duplicate section.
"""
        findings = validate_human_facing_markdown(markdown)

        self.assertTrue(any("truncation" in finding.lower() for finding in findings))
        self.assertTrue(any("dead numeric citation" in finding.lower() for finding in findings))
        self.assertTrue(any("bracketed source id" in finding.lower() for finding in findings))
        self.assertTrue(any("raw dict" in finding.lower() for finding in findings))
        self.assertTrue(any("duplicate" in finding.lower() for finding in findings))
        self.assertTrue(any("status-only" in finding.lower() for finding in findings))


if __name__ == "__main__":
    unittest.main()
