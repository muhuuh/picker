from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from stock_research.human_synthesis_pack import build_human_synthesis_packs


class HumanSynthesisPackTests(unittest.TestCase):
    def test_builds_first_principles_synthesis_pack(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_id = "2026-05-16_weekly"
            seed_synthesis_inputs(root, run_id, "AMBA")

            result = build_human_synthesis_packs(root, run_id, tickers=["AMBA"], write=True)

            self.assertEqual(result.status, "ready")
            self.assertEqual(len(result.packs), 1)
            pack = result.packs[0]
            pack_text = (root / pack.synthesis_pack_path).read_text(encoding="utf-8")
            self.assertIn("Write the final human-facing report from scratch", pack_text)
            self.assertIn("Use the established final-report shape from the accepted AMBA report", pack_text)
            self.assertIn("The deterministic opportunity assessment remains the audit artifact", pack_text)
            self.assertIn("What [Company] Actually Does", pack_text)
            self.assertIn("preserve at least the same investor-useful insight coverage as the opportunity assessment", pack_text)
            self.assertIn("notable accounts/posts or source-quality context", pack_text)
            self.assertIn("decision table or scorecard", pack_text)
            self.assertIn("deterministic opportunity assessment is an evidence and audit layer", pack_text)
            self.assertIn("Auxiliary Grok Web Inputs", pack_text)
            self.assertIn("Expected final report", pack_text)

    def test_collects_slugged_grok_artifacts_for_dotted_ticker(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_id = "2026-05-18_manual"
            ticker = "LPK.DE"
            seed_synthesis_inputs(root, run_id, ticker)
            raw_dir = root / "agents" / "runs" / run_id / "raw" / "xai_grok"
            (raw_dir / "xai_x_search_company_lpk_de.json").write_text("{}", encoding="utf-8")
            (raw_dir / "xai_web_deep_dive_company_lpk_de.json").write_text("{}", encoding="utf-8")

            result = build_human_synthesis_packs(root, run_id, tickers=[ticker], write=True)

            self.assertEqual(result.status, "ready")
            pack_text = (root / result.packs[0].synthesis_pack_path).read_text(encoding="utf-8")
            self.assertIn("xai_x_search_company_lpk_de.json", pack_text)
            self.assertIn("xai_web_deep_dive_company_lpk_de.json", pack_text)


def seed_synthesis_inputs(root: Path, run_id: str, ticker: str) -> None:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking" / "stock_info_files" / "current_holdings").mkdir(parents=True)
    (root / "stock_tracking" / "stock_info_files" / "current_holdings" / f"{ticker}.md").write_text(
        "# AMBA\n\nPrior thesis.\n",
        encoding="utf-8",
    )
    run_dir = root / "agents" / "runs" / run_id
    (run_dir / "reports" / "opportunity_assessment").mkdir(parents=True)
    (run_dir / "reports" / "financial_data_specialist").mkdir(parents=True)
    (run_dir / "reports" / "company_news_specialist").mkdir(parents=True)
    (run_dir / "raw" / "opportunity_assessment").mkdir(parents=True)
    (run_dir / "raw" / "xai_grok").mkdir(parents=True)
    (run_dir / "reports" / "opportunity_assessment" / f"{ticker}_opportunity_assessment.md").write_text("# audit\n", encoding="utf-8")
    (run_dir / "reports" / "financial_data_specialist" / f"{ticker}_financial_review.md").write_text("# financial\n", encoding="utf-8")
    (run_dir / "reports" / "company_news_specialist" / f"{ticker}_company_news_review.md").write_text("# news\n", encoding="utf-8")
    (run_dir / "raw" / "xai_grok" / "web_search_company_deep_dive_amba.json").write_text("{}", encoding="utf-8")
    assessment = {
        "ticker": ticker,
        "opportunity_view": "watch_closely",
        "opportunity_score": 72,
        "risk_level": "medium",
        "confidence": "medium",
        "thesis_freshness": "fresh",
        "summary": "AMBA needs verification but has a clearer edge-AI narrative.",
        "recommended_next_action": "Read the next earnings transcript.",
        "financial_snapshot": {"status": "available", "latest_price": 81.16, "market_cap": 3550000000},
        "news_snapshot": {
            "status": "available",
            "source_count": 2,
            "material_developments": [{"claim": "FY2026 revenue grew 37.2%."}],
        },
        "social_snapshot": {
            "status": "available",
            "sentiment": "bullish_social_signal",
            "x_pulse": "X narrative moved toward physical AI.",
            "bullish_claims": ["Low-power vision SoCs fit robotics constraints."],
            "bearish_claims": ["Robotics revenue proof is still thin."],
        },
        "grok_web_snapshot": {
            "status": "available",
            "business_technology_overview": "Low-power edge-AI SoCs.",
            "financial_snapshot": "Market cap around $3.5B.",
            "analyst_forecasts": "Average target around $96.",
        },
        "positives": ["Edge-AI mix is now material."],
        "negatives": ["Valuation needs growth proof."],
        "watch_items": ["Verify named robotics design wins."],
    }
    (run_dir / "raw" / "opportunity_assessment" / f"{ticker}_opportunity_assessment.json").write_text(
        json.dumps(assessment),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
