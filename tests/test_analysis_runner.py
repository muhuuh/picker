from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.analysis_runner import run_analysis_tasks
from stock_research.evidence import Claim, Source, read_packet, validate_packet, write_packet, new_packet


class AnalysisRunnerTests(unittest.TestCase):
    def test_dry_run_lists_analysis_tasks_in_dependency_order(self):
        manifest = manifest_with_financial_tasks()

        result = run_analysis_tasks(Path("."), manifest, execute=False)

        self.assertEqual(result["mode"], "dry_run")
        self.assertEqual([task["id"] for task in result["planned"]], ["financial_compare_aapl", "financial_review_aapl"])

    def test_execute_runs_financial_compare_then_review(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            run_id = "2026-05-09_weekly"
            write_input_packet(root, run_id, "fmp", {"price": 100.0, "market_cap": 1000, "pe_ratio_ttm": 20.0, "currency": "USD"})
            write_input_packet(root, run_id, "alpha_vantage", {"latest_price": "100.5", "market_cap": "1010", "pe_ratio": "20.4", "currency": "USD"})
            write_input_packet(root, run_id, "polygon", {"previous_close": 100.2, "market_cap": 1005, "currency": "usd", "primary_exchange": "XNAS"})

            result = run_analysis_tasks(root, manifest_with_financial_tasks(), execute=True, current_date=date(2026, 5, 4))

            self.assertEqual(len(result["executed"]), 2)
            self.assertFalse(result["errors"])
            self.assertFalse(result["skipped"])
            review_packet_path = root / "agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_financial_data_specialist_company_aapl.json"
            self.assertTrue(review_packet_path.exists())
            self.assertTrue(validate_packet(read_packet(review_packet_path)).ok)

    def test_execute_skips_selected_dependent_task_when_dependency_fails(self):
        def failing_executor(_root, task, _current_date):
            if task["id"] == "financial_compare_aapl":
                raise RuntimeError("compare failed")
            return {"packet_id": "unused", "paths": []}

        result = run_analysis_tasks(Path("."), manifest_with_financial_tasks(), execute=True, executor=failing_executor)

        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["skipped"][0]["id"], "financial_review_aapl")
        self.assertEqual(result["skipped"][0]["blocked_by"], ["financial_compare_aapl"])


def seed_repo(root: Path) -> Path:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking").mkdir(parents=True)
    (root / "agents/runs/2026-05-09_weekly/evidence_packets").mkdir(parents=True)
    return root


def manifest_with_financial_tasks() -> dict:
    return {
        "manifest_id": "weekly_2026-05-09",
        "analysis_tasks": [
            {
                "id": "financial_review_aapl",
                "tool": "financial_review",
                "subject_type": "company",
                "subject_id": "AAPL",
                "priority": "high",
                "args": {"ticker": "AAPL", "run_id": "2026-05-09_weekly"},
                "depends_on": ["financial_compare_aapl"],
                "reason": "Review AAPL financial comparison.",
            },
            {
                "id": "financial_compare_aapl",
                "tool": "financial_compare",
                "subject_type": "company",
                "subject_id": "AAPL",
                "priority": "high",
                "args": {"ticker": "AAPL", "run_id": "2026-05-09_weekly"},
                "depends_on": ["provider_tasks"],
                "reason": "Compare AAPL financial packets.",
            },
        ],
    }


def write_input_packet(root: Path, run_id: str, provider: str, metrics: dict):
    packet = new_packet(
        provider=provider,
        subject_type="company",
        subject_id="AAPL",
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
                evidence=json.dumps(metrics),
                source_ids=[f"{provider}_source"],
                confidence="medium",
                impact="medium",
            )
        ],
    )
    path = root / "agents" / "runs" / run_id / "evidence_packets" / f"{provider}.json"
    write_packet(packet, path)
    return path


if __name__ == "__main__":
    unittest.main()
