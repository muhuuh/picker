from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.company_file_factual_update import build_company_file_factual_updates


class CompanyFileFactualUpdateTests(unittest.TestCase):
    def test_dry_run_does_not_write_company_file(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))

            result = build_company_file_factual_updates(
                root=root,
                run_id="2026-05-16_weekly",
                current_date=date(2026, 5, 16),
            )

            self.assertEqual(result.status, "ready_to_apply")
            text = (root / "stock_tracking/stock_info_files/current_holdings/AMZN.md").read_text(encoding="utf-8")
            self.assertNotIn("AUTOFACT-2026-05-16_weekly-AMZN", text)

    def test_write_applies_factual_rows_and_is_idempotent(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))

            result = build_company_file_factual_updates(
                root=root,
                run_id="2026-05-16_weekly",
                current_date=date(2026, 5, 16),
                write=True,
            )
            second = build_company_file_factual_updates(
                root=root,
                run_id="2026-05-16_weekly",
                current_date=date(2026, 5, 16),
                write=True,
            )

            self.assertEqual(result.status, "complete")
            self.assertEqual(second.items[0].status, "already_applied")
            company_text = (root / "stock_tracking/stock_info_files/current_holdings/AMZN.md").read_text(encoding="utf-8")
            self.assertIn("## Automated Factual Updates", company_text)
            self.assertGreaterEqual(company_text.count("AUTOFACT-2026-05-16_weekly-AMZN"), 6)
            self.assertIn("AWS +28% YoY", company_text)
            self.assertTrue((root / "agents/runs/2026-05-16_weekly/company_file_factual_updates.md").exists())

    def test_quality_findings_block_write(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir), quality_findings=["missing source links"])

            result = build_company_file_factual_updates(
                root=root,
                run_id="2026-05-16_weekly",
                current_date=date(2026, 5, 16),
                write=True,
            )

            self.assertEqual(result.status, "blocked")
            text = (root / "stock_tracking/stock_info_files/current_holdings/AMZN.md").read_text(encoding="utf-8")
            self.assertNotIn("AUTOFACT-2026-05-16_weekly-AMZN", text)


def seed_repo(root: Path, quality_findings: list[str] | None = None) -> Path:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking/current_holdings").mkdir(parents=True)
    (root / "stock_tracking/monitoring").mkdir(parents=True)
    (root / "stock_tracking/rejected").mkdir(parents=True)
    (root / "stock_tracking/stock_info_files/current_holdings").mkdir(parents=True)
    (root / "docs/plans").mkdir(parents=True)
    (root / "strategy").mkdir(parents=True)
    (root / "agents/runs/2026-05-16_weekly/raw/opportunity_assessment").mkdir(parents=True)
    (root / "agents/runs/2026-05-16_weekly/reports/opportunity_assessment").mkdir(parents=True)
    write_stock_csv(
        root / "stock_tracking/current_holdings/current_holdings.csv",
        [
            "AMZN,Amazon.com Inc.,NASDAQ,US,Technology,Internet,current_holding,stock_tracking/stock_info_files/current_holdings/AMZN.md"
        ],
    )
    write_stock_csv(root / "stock_tracking/monitoring/monitoring.csv", [])
    write_stock_csv(root / "stock_tracking/rejected/rejected.csv", [])
    (root / "docs/plans/human_research_requests.md").write_text("# Human Research Requests\n", encoding="utf-8")
    (root / "strategy/research_priorities.md").write_text("# Research Priorities\n", encoding="utf-8")
    (root / "agents/human_review_queue.md").write_text("# Human Review Queue\n", encoding="utf-8")
    (root / "stock_tracking/stock_info_files/current_holdings/AMZN.md").write_text(
        "\n".join(
            [
                "# AMZN - Amazon.com Inc.",
                "",
                "Last updated: 2026-05-01",
                "",
                "## Source Log",
                "",
                "| Date | Source | Type | Relevance | Link / Location |",
                "| --- | --- | --- | --- | --- |",
                "",
                "## Change Log",
                "",
                "| Date | Updated by | Change | Reason / Source |",
                "| --- | --- | --- | --- |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assessment = {
        "ticker": "AMZN",
        "status": "ready_for_human_review",
        "quality_findings": quality_findings or [],
        "summary": "AMZN is interesting because AWS re-acceleration and AI infrastructure optionality improved.",
        "financial_snapshot": {
            "latest_price": 220.1,
            "market_cap": 2300000000000,
            "pe_ratio": 32.4,
            "forward_pe": 28.1,
            "quarterly_revenue_growth_yoy": "17%",
            "operating_margin_ttm": "13.1%",
            "analyst_target_price": 255,
            "analyst_target_implied_upside": "16%",
        },
        "news_snapshot": {"material_developments": ["AWS +28% YoY", "Anthropic investment remains strategically relevant"]},
        "social_snapshot": {
            "sentiment": "constructive",
            "x_pulse": "X debate focuses on AWS AI demand versus capex risk.",
            "bullish_claims": ["Trainium and Bedrock momentum"],
            "bearish_claims": ["AI capex may pressure FCF"],
        },
        "watch_items": ["Verify AWS growth stays above 25%", "Track capex/free-cash-flow conversion"],
    }
    (root / "agents/runs/2026-05-16_weekly/raw/opportunity_assessment/AMZN_opportunity_assessment.json").write_text(
        json.dumps(assessment),
        encoding="utf-8",
    )
    (root / "agents/runs/2026-05-16_weekly/reports/opportunity_assessment/AMZN_opportunity_assessment.md").write_text(
        "# AMZN Opportunity Assessment\n",
        encoding="utf-8",
    )
    return root


def write_stock_csv(path: Path, rows: list[str]) -> None:
    header = "ticker,company_name,exchange,country,sector,industry,status,stock_info_file"
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
