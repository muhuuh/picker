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

    def test_concise_source_specific_final_human_report_contract_passes_without_padding(self):
        markdown = """
# AMBA Final Human Report

Generated: 2026-05-18

This report is a Codex-written synthesis from the synthesis pack, deterministic audit report, company-news and financial specialist outputs, raw Grok/X sentiment, the live Grok web deep dive, and the current company file. It is written as the human-facing read. The deterministic opportunity assessment remains the audit artifact.

## Bottom Line

AMBA is a watchlist-quality idea because edge-AI demand improved, while proof still depends on revenue conversion.

## What Ambarella Actually Does

Ambarella sells low-power vision processors for cameras, vehicles, robotics, and edge devices.

## Why The Setup Changed

The setup changed because recent evidence points to stronger edge-AI interest and better near-term customer activity.

## X Sentiment And What It Is Really Saying

X is useful as a narrative check here, not as proof. The main debate is whether robotics demand becomes material. Notable accounts/posts worth reviewing include informed accounts that discuss edge-AI design wins, and the report separates recurring accounts from price-action noise.

Rumors and unverified claims are separated from facts: humanoid-volume speculation remains speculation until customer programs or company filings confirm it.

Non-obvious / under-discussed angles include the low-power memory-cost constraint for physical AI and hidden optionality if robotics customers need local perception at low heat.

## Financial And Valuation Read

The valuation needs growth proof because the business is still being valued on future AI adoption.

## Bull Case

The bull case is that edge-AI design wins compound into visible revenue.

## Bear Case

The bear case is that customer interest stays stuck in trials and does not reach production volume.

## What Would Change The Thesis

Named production wins or weaker order data would change the thesis.

## Next Research Checks

Read the next earnings transcript and verify named customer programs.

| Signal | Evidence | Confidence | What confirms it | What invalidates it |
| --- | --- | --- | --- | --- |
| Edge-AI conversion | Source-backed facts plus X narrative | Medium | Named design wins | Generic AI language only |

## Final Assessment

The report view is constructive but not yet decisive. This fuller paragraph exists so the test report is long enough to represent a real final human report rather than a shallow status summary. It repeats the depth expectation in plain terms: final reports must keep source-backed facts, social narrative, rumors, non-obvious angles, valuation gaps, scorecards, thesis changers, and concrete checks visible to the reader. The writer should remove duplication, but not remove the actual investor insight.

Additional depth text: A proper report should explain what the company does, why the setup changed, how verified facts differ from X/social claims, which claims are rumor-like, what would make the thesis stronger, and what would make it weaker. It should also preserve enough company, market, financial, and sentiment detail that the reader does not need to open the deterministic audit artifact just to understand the investment debate. The final report is a cleaner story, not a smaller story. It keeps the opportunity assessment's useful information while avoiding pasted sections and repeated claims. This paragraph intentionally carries enough words for the quality gate to model a human-useful report.

## Sources

- [AMBA synthesis pack](agents/runs/2026-05-16_weekly/reports/human_synthesis/AMBA_synthesis_pack.md)
"""
        self.assertEqual(validate_human_facing_markdown(markdown), [])

    def test_flags_final_human_report_missing_established_contract(self):
        markdown = """
# LPK.DE Final Human Report

## Thesis

LPKF has an interesting packaging story, but the report did not follow the established shape.
"""
        findings = validate_human_facing_markdown(markdown)

        self.assertTrue(any("provenance" in finding.lower() for finding in findings))
        self.assertTrue(any("audit artifact" in finding.lower() for finding in findings))
        self.assertTrue(any("established synthesis sections" in finding.lower() for finding in findings))

    def test_flags_truncation_dead_citations_raw_dict_and_status_only_sentiment(self):
        markdown = """
# Bad Report

## News

Narrative is gaining ste...
Grok/X social signal: mixed_social_signal
Raw item: {'claim': 'AWS grew', 'confidence': 'medium'}
Source: [xai_x_source_1]
Another dead marker [1]
Encoding artifact: \u00e2\u20ac\u00a2 Revenue.
Fragment: gross margin expanded to 62% (up.

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
        self.assertTrue(any("mojibake" in finding.lower() for finding in findings))
        self.assertTrue(any("dangling" in finding.lower() for finding in findings))

    def test_flags_repeated_long_claims(self):
        markdown = """
# Bad Repetition

## First

- Ambarella revenue accelerated because edge AI camera demand improved and management raised near-term product expectations.

## Second

- Ambarella revenue accelerated because edge AI camera demand improved and management raised near-term product expectations.
"""
        findings = validate_human_facing_markdown(markdown)

        self.assertTrue(any("repeated long claims" in finding.lower() for finding in findings))

    def test_flags_incomplete_bullets_and_table_cells(self):
        markdown = """
# Incomplete Evidence

## Evidence

- Management described demand from.

| Signal | Evidence |
| --- | --- |
| AI demand | Customers increasingly sh. |
"""

        findings = validate_human_facing_markdown(markdown)

        self.assertIn("Dangling sentence fragment found.", findings)


if __name__ == "__main__":
    unittest.main()
