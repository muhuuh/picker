from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.scheduled_runner import run_weekly_research_workflow


class ScheduledRunnerTests(unittest.TestCase):
    def test_weekly_workflow_dry_run_reaches_framework_boundary_without_writing(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))

            result, paths = run_weekly_research_workflow(root=root, current_date=date(2026, 5, 5))

            self.assertEqual(result.status, "dry_run")
            self.assertEqual(paths, [])
            self.assertEqual(result.steps["framework_boundary"]["status"], "pending_decision")
            self.assertFalse((root / "agents/runs/2026-05-09_weekly/manifest.json").exists())

    def test_weekly_workflow_write_persists_final_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))

            result, paths = run_weekly_research_workflow(root=root, current_date=date(2026, 5, 5), write=True)

            self.assertEqual(result.status, "complete")
            self.assertTrue(paths)
            self.assertTrue((root / "agents/runs/2026-05-09_weekly/manifest.json").exists())
            self.assertTrue((root / "agents/runs/2026-05-09_weekly/run_summary.md").exists())
            self.assertTrue((root / "agents/runs/2026-05-09_weekly/quality_report.md").exists())
            self.assertTrue((root / "agents/runs/2026-05-09_weekly/finalization.md").exists())
            self.assertTrue((root / "agents/runs/2026-05-09_weekly/memory_writer_review.md").exists())
            self.assertTrue((root / "agents/runs/2026-05-09_weekly/orchestration_report.md").exists())

    def test_weekly_workflow_can_execute_with_injected_task_executors(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir), monitoring_rows=["AAPL,Apple Inc.,NASDAQ,US,Technology,Consumer Electronics,monitoring,test,100,USD,1000,20,2026-05-01,2026-05-01,2026-05-09,stock_tracking/stock_info_files/monitoring/AAPL_apple_inc.md,test"])

            result, _paths = run_weekly_research_workflow(
                root=root,
                current_date=date(2026, 5, 5),
                execute_providers=True,
                execute_analysis=True,
                provider_executor=fake_provider_executor,
                analysis_executor=fake_analysis_executor,
            )

            self.assertEqual(result.status, "dry_run")
            self.assertGreater(len(result.steps["provider_tasks"]["executed"]), 0)
            self.assertGreater(len(result.steps["analysis_tasks"]["executed"]), 0)


def seed_repo(root: Path, monitoring_rows: list[str] | None = None) -> Path:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking/current_holdings").mkdir(parents=True)
    (root / "stock_tracking/monitoring").mkdir(parents=True)
    (root / "stock_tracking/rejected").mkdir(parents=True)
    (root / "stock_tracking/stock_info_files/monitoring").mkdir(parents=True)
    (root / "agents/memory").mkdir(parents=True)
    (root / "docs/plans").mkdir(parents=True)
    (root / "strategy").mkdir(parents=True)
    write_stock_csv(root / "stock_tracking/current_holdings/current_holdings.csv", [])
    write_stock_csv(root / "stock_tracking/monitoring/monitoring.csv", monitoring_rows or [])
    write_stock_csv(root / "stock_tracking/rejected/rejected.csv", [])
    (root / "docs/plans/human_research_requests.md").write_text("# Human Research Requests\n", encoding="utf-8")
    (root / "strategy/research_priorities.md").write_text("# Research Priorities\n", encoding="utf-8")
    (root / "agents/human_review_queue.md").write_text("# Human Review Queue\n", encoding="utf-8")
    return root


def write_stock_csv(path: Path, rows: list[str]) -> None:
    header = "ticker,company_name,exchange,country,sector,industry,status,source,price,currency,market_cap,pe_ratio,date_found,date_last_updated,next_review_date,stock_info_file,notes"
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")


def fake_provider_executor(root: Path, task: dict, current_date: date | None):
    return {"packet_id": f"packet_{task['id']}", "paths": [str(root / "fake_provider.json")]}


def fake_analysis_executor(root: Path, task: dict, current_date: date | None):
    return {"packet_id": f"packet_{task['id']}", "paths": [str(root / "fake_analysis.json")]}


if __name__ == "__main__":
    unittest.main()
