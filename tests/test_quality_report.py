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

    def test_quality_report_checks_final_human_reports(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            run_dir = root / "agents/runs/2026-05-09_weekly"
            (run_dir / "manifest.json").write_text(json.dumps({"provider_tasks": [], "analysis_tasks": []}), encoding="utf-8")
            (run_dir / "run_summary.md").write_text("# Summary\n", encoding="utf-8")
            human_synthesis_dir = run_dir / "reports" / "human_synthesis"
            human_synthesis_dir.mkdir(parents=True)
            repeated_claim = (
                "AMBA needs to prove that edge AI design wins can convert into durable revenue growth "
                "before valuation risk becomes acceptable."
            )
            (human_synthesis_dir / "AMBA_final_human_report.md").write_text(
                f"# AMBA Final Human Report\n\n## Thesis\n\n{repeated_claim}\n\n## Next Checks\n\n{repeated_claim}\n",
                encoding="utf-8",
            )
            (human_synthesis_dir / "AMBA_synthesis_pack.md").write_text(
                f"# AMBA Synthesis Pack\n\n## Inputs\n\n{repeated_claim}\n\n## Audit\n\n{repeated_claim}\n",
                encoding="utf-8",
            )

            report = build_quality_report(root, "2026-05-09_weekly", date(2026, 5, 4))

            quality_findings = [finding for finding in report.findings if finding.category == "human_report_quality"]
            self.assertTrue(any("Repeated long claims found" in finding.summary for finding in quality_findings))
            self.assertTrue(any("established synthesis sections" in finding.summary for finding in quality_findings))
            self.assertTrue(all("AMBA_final_human_report.md" in finding.evidence for finding in quality_findings))
            self.assertTrue(all("AMBA_synthesis_pack.md" not in finding.evidence for finding in quality_findings))

    def test_quality_report_can_require_canonical_final_reports_after_codex(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            run_dir = root / "agents/runs/2026-05-09_weekly"
            (run_dir / "manifest.json").write_text(json.dumps({"provider_tasks": [], "analysis_tasks": []}), encoding="utf-8")
            (run_dir / "run_summary.md").write_text("# Summary\n", encoding="utf-8")
            human_synthesis_dir = run_dir / "reports" / "human_synthesis"
            human_synthesis_dir.mkdir(parents=True)
            (human_synthesis_dir / "AMBA_synthesis_pack.md").write_text("# AMBA Synthesis Pack\n", encoding="utf-8")

            pre_codex_report = build_quality_report(root, "2026-05-09_weekly", date(2026, 5, 4))
            post_codex_report = build_quality_report(
                root,
                "2026-05-09_weekly",
                date(2026, 5, 4),
                require_final_reports=True,
            )

            self.assertFalse(any(finding.category == "missing_final_human_report" for finding in pre_codex_report.findings))
            self.assertTrue(any(finding.category == "missing_final_human_report" for finding in post_codex_report.findings))
            self.assertTrue(any("AMBA_final_human_report.md" in finding.evidence for finding in post_codex_report.findings))

    def test_quality_report_flags_boilerplate_repeated_across_final_reports(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            run_dir = root / "agents/runs/2026-05-09_weekly"
            (run_dir / "manifest.json").write_text(json.dumps({"provider_tasks": [], "analysis_tasks": []}), encoding="utf-8")
            (run_dir / "run_summary.md").write_text("# Summary\n", encoding="utf-8")
            human_synthesis_dir = run_dir / "reports" / "human_synthesis"
            human_synthesis_dir.mkdir(parents=True)
            shared = (
                "The key judgment is whether the story is becoming more verified or merely louder. "
                "The company news lane supplies facts while the social lane supplies investor debate."
            )
            for ticker in ("ALPHA", "BRAVO", "CHARLIE"):
                (human_synthesis_dir / f"{ticker}_final_human_report.md").write_text(
                    f"# {ticker} Final Human Report\n\n## Bottom Line\n\n{shared}\n",
                    encoding="utf-8",
                )

            report = build_quality_report(root, "2026-05-09_weekly", date(2026, 5, 4))

            corpus_findings = [finding for finding in report.findings if finding.category == "cross_report_boilerplate"]
            self.assertGreaterEqual(len(corpus_findings), 1)
            self.assertEqual(report.metrics["cross_report_findings"], len(corpus_findings))
            self.assertTrue(all(ticker in corpus_findings[0].evidence for ticker in ("ALPHA", "BRAVO", "CHARLIE")))

    def test_quality_report_flags_orphan_final_reports(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            run_dir = root / "agents/runs/2026-05-09_weekly"
            (run_dir / "manifest.json").write_text(json.dumps({"provider_tasks": [], "analysis_tasks": []}), encoding="utf-8")
            (run_dir / "run_summary.md").write_text("# Summary\n", encoding="utf-8")
            human_synthesis_dir = run_dir / "reports" / "human_synthesis"
            human_synthesis_dir.mkdir(parents=True)
            (human_synthesis_dir / "RANDOM_final_human_report.md").write_text("# RANDOM Final Human Report\n", encoding="utf-8")

            report = build_quality_report(root, "2026-05-09_weekly", date(2026, 5, 4))

            self.assertTrue(any(finding.category == "orphan_final_human_report" for finding in report.findings))

    def test_quality_report_checks_human_review_digest(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            run_dir = root / "agents/runs/2026-05-09_weekly"
            (run_dir / "manifest.json").write_text(json.dumps({"provider_tasks": [], "analysis_tasks": []}), encoding="utf-8")
            (run_dir / "run_summary.md").write_text("# Summary\n", encoding="utf-8")
            (root / "agents/human_review_digest.md").write_text(
                "# Human Review Digest\n\n## Review\n\nThis row has a visible truncation marker [...]\n",
                encoding="utf-8",
            )

            report = build_quality_report(root, "2026-05-09_weekly", date(2026, 5, 4))

            quality_findings = [finding for finding in report.findings if finding.category == "human_report_quality"]
            self.assertEqual(len(quality_findings), 1)
            self.assertIn("Visible truncation marker found", quality_findings[0].summary)
            self.assertIn("agents/human_review_digest.md", quality_findings[0].evidence)


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
