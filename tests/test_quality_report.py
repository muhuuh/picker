from datetime import date
from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.evidence import Claim, Source, new_packet, write_packet
from stock_research.quality_report import build_quality_report, write_quality_report


class QualityReportTests(unittest.TestCase):
    def test_quality_report_flags_missing_provider_packet_and_writes_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            write_manifest(root)
            write_packet_for_provider(root, "yfinance", "AAPL")
            (root / "agents/runs/2026-05-09_weekly/run_summary.md").write_text("# Summary\n", encoding="utf-8")

            report = build_quality_report(root, "2026-05-09_weekly", date(2026, 5, 4))
            json_path, md_path = write_quality_report(root, report)

            self.assertEqual(report.metrics["evidence_packets"], 1)
            self.assertTrue(any(finding.category == "planned_provider_task_without_packet" for finding in report.findings))
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

    def test_quality_report_distinguishes_exa_tasks_for_same_subject(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            manifest = {
                "provider_tasks": [
                    {
                        "id": "exa_research_priority_stock_discovery",
                        "provider": "exa",
                        "tool": "search",
                        "subject_type": "theme",
                        "subject_id": "stock_discovery",
                        "args": {"mode": "general"},
                    },
                    {
                        "id": "exa_discovery_priority_stock_discovery",
                        "provider": "exa",
                        "tool": "search",
                        "subject_type": "theme",
                        "subject_id": "stock_discovery",
                        "args": {"mode": "company"},
                    },
                ],
                "analysis_tasks": [],
            }
            (root / "agents/runs/2026-05-09_weekly/manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (root / "agents/runs/2026-05-09_weekly/run_summary.md").write_text("# Summary\n", encoding="utf-8")
            packet = new_packet(provider="exa", subject_type="theme", subject_id="stock_discovery", current_date=date(2026, 5, 4))
            packet = replace(packet, packet_id=f"{packet.packet_id}_exa_research_priority_stock_discovery")
            write_packet(packet, root / "agents/runs/2026-05-09_weekly/evidence_packets/exa_general.json")

            report = build_quality_report(root, "2026-05-09_weekly", date(2026, 5, 4))

            missing = [finding.summary for finding in report.findings if finding.category == "planned_provider_task_without_packet"]
            self.assertEqual(len(missing), 1)
            self.assertIn("exa_discovery_priority_stock_discovery", missing[0])


def seed_repo(root: Path) -> Path:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking").mkdir(parents=True)
    (root / "agents/runs/2026-05-09_weekly/evidence_packets").mkdir(parents=True)
    return root


def write_manifest(root: Path) -> None:
    manifest = {
        "provider_tasks": [
            {"id": "yfinance_company_aapl", "provider": "yfinance", "subject_id": "AAPL"},
            {"id": "exa_news_company_aapl", "provider": "exa", "subject_id": "AAPL"},
        ],
        "analysis_tasks": [],
    }
    (root / "agents/runs/2026-05-09_weekly/manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def write_packet_for_provider(root: Path, provider: str, ticker: str) -> None:
    packet = new_packet(
        provider=provider,
        subject_type="company",
        subject_id=ticker,
        current_date=date(2026, 5, 4),
        sources=[
            Source(
                source_id=f"{provider}_source",
                provider=provider,
                source_type="market_data",
                artifact_path=f"raw/{provider}.json",
            )
        ],
        claims=[
            Claim(
                claim=f"{provider} snapshot",
                evidence="{}",
                source_ids=[f"{provider}_source"],
                confidence="medium",
                impact="medium",
            )
        ],
    )
    write_packet(packet, root / f"agents/runs/2026-05-09_weekly/evidence_packets/{provider}.json")


if __name__ == "__main__":
    unittest.main()
