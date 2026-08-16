from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.evidence import Claim, Source, new_packet, write_packet
from stock_research.run_summary import build_run_summary, write_run_summary


class RunSummaryTests(unittest.TestCase):
    def test_run_summary_extracts_financial_review_status_and_writes_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            write_manifest(root)
            write_financial_review_packet(root)

            summary = build_run_summary(root, "2026-05-09_weekly", date(2026, 5, 4))
            json_path, md_path = write_run_summary(root, summary)

            self.assertEqual(summary.metrics["evidence_packets"], 1)
            self.assertEqual(summary.financial_reviews[0]["ticker"], "AAPL")
            self.assertEqual(summary.financial_reviews[0]["status"], "ready_for_company_update")
            self.assertEqual(summary.recurring_coverage["industry_cluster_count"], 1)
            self.assertEqual(summary.recurring_coverage["comparison_status"], "not_recorded")
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())
            markdown = md_path.read_text(encoding="utf-8")
            self.assertIn("Run Summary", markdown)
            self.assertIn("Semiconductors: AAPL", markdown)


def seed_repo(root: Path) -> Path:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking").mkdir(parents=True)
    (root / "agents/runs/2026-05-09_weekly/evidence_packets").mkdir(parents=True)
    return root


def write_manifest(root: Path) -> None:
    manifest = {
        "provider_tasks": [{"id": "yfinance_company_aapl"}],
        "analysis_tasks": [{"id": "financial_review_aapl"}],
        "tracked_tickers": {"monitoring": ["AAPL"]},
        "research_profile": "portfolio_update",
        "recurring_coverage": {
            "companies": [{"ticker": "AAPL"}],
            "industry_clusters": [
                {
                    "cluster_id": "semiconductors",
                    "label": "Semiconductors",
                    "member_tickers": ["AAPL"],
                }
            ],
            "impact_basis": "membership_only",
            "weights_available": False,
            "comparison_baseline": {
                "policy": "explicit_acceptance_only",
                "status": "not_recorded",
                "comparison_run_id": "",
                "latest_generated_run_id": "2026-05-02_weekly",
            },
        },
    }
    (root / "agents/runs/2026-05-09_weekly/manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def write_financial_review_packet(root: Path) -> None:
    packet = new_packet(
        provider="financial_data_specialist",
        subject_type="company",
        subject_id="AAPL",
        current_date=date(2026, 5, 4),
        sources=[
            Source(
                source_id="financial_specialist_report",
                provider="financial_data_specialist",
                source_type="internal",
                artifact_path="agents/runs/2026-05-09_weekly/reports/financial_data_specialist/AAPL_financial_review.md",
            )
        ],
        claims=[
            Claim(
                claim="Financial data specialist review completed for AAPL.",
                evidence=json.dumps({"status": "ready_for_company_update"}),
                source_ids=["financial_specialist_report"],
                confidence="high",
                impact="medium",
            )
        ],
    )
    write_packet(packet, root / "agents/runs/2026-05-09_weekly/evidence_packets/financial_review.json")


if __name__ == "__main__":
    unittest.main()
