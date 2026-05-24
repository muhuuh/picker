from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.artifact_hygiene import archive_artifacts, build_artifact_inventory, cleanup_runtime_json


class ArtifactHygieneTests(unittest.TestCase):
    def test_inventory_classifies_active_review_blocked_and_archive_candidates(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))

            result = build_artifact_inventory(
                root=root,
                current_date=date(2026, 5, 16),
                archive_after_days=7,
                write=True,
            )

            by_path = {item.path: item for item in result.items}
            self.assertEqual(
                by_path["agents/runs/2026-04-01_weekly/reports/opportunity_assessment/AMZN_opportunity_assessment.md"].status,
                "active_keep",
            )
            self.assertEqual(
                by_path["agents/runs/2026-04-01_weekly/market_research/candidate_review.md"].status,
                "review_blocked",
            )
            self.assertEqual(
                by_path["agents/runs/2026-04-01_weekly/reports/opportunity_assessment/OLD_opportunity_assessment.md"].status,
                "archive_candidate",
            )
            self.assertTrue((root / "archive/research_index.md").exists())

    def test_archive_moves_only_archive_candidates_and_refreshes_index(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))

            dry_run = archive_artifacts(
                root=root,
                current_date=date(2026, 5, 16),
                archive_after_days=7,
            )
            result = archive_artifacts(
                root=root,
                current_date=date(2026, 5, 16),
                archive_after_days=7,
                write=True,
            )

            archived_path = root / "archive/runs/2026/2026-04-01_weekly/reports/opportunity_assessment/OLD_opportunity_assessment.md"
            active_path = root / "agents/runs/2026-04-01_weekly/reports/opportunity_assessment/AMZN_opportunity_assessment.md"
            blocked_path = root / "agents/runs/2026-04-01_weekly/market_research/candidate_review.md"

            self.assertEqual(dry_run.status, "ready_to_archive")
            self.assertEqual(result.status, "complete")
            self.assertTrue(archived_path.exists())
            self.assertFalse((root / "agents/runs/2026-04-01_weekly/reports/opportunity_assessment/OLD_opportunity_assessment.md").exists())
            self.assertTrue(active_path.exists())
            self.assertTrue(blocked_path.exists())
            self.assertTrue((root / "archive/archive_move_report.md").exists())
            self.assertIn("archived", (root / "archive/research_index.md").read_text(encoding="utf-8"))

    def test_runtime_json_cleanup_deletes_only_finalized_old_unblocked_runs(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            finalized_run = seed_finalized_run(root, "2026-04-01_old-finalized")
            recent_run = seed_finalized_run(root, "2026-05-20_recent-finalized")
            blocked_run = seed_finalized_run(root, "2026-04-01_review-blocked")
            (root / "agents/human_review_queue.md").write_text(
                "\n".join(
                    [
                        "# Human Review Queue",
                        "",
                        "| ID | Type | Status | Decision Needed | Evidence |",
                        "| --- | --- | --- | --- | --- |",
                        "| HRQ-1 | candidate_verification | open | decide | agents/runs/2026-04-01_review-blocked/final_digest.md |",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            dry_run = cleanup_runtime_json(
                root=root,
                current_date=date(2026, 5, 24),
                retention_days=7,
            )
            result = cleanup_runtime_json(
                root=root,
                current_date=date(2026, 5, 24),
                retention_days=7,
                write=True,
            )

            by_run = {run.run_id: run for run in result.runs}
            self.assertEqual(dry_run.status, "partial")
            self.assertEqual(by_run["2026-04-01_old-finalized"].status, "deleted")
            self.assertEqual(by_run["2026-05-20_recent-finalized"].status, "recent_keep")
            self.assertEqual(by_run["2026-04-01_review-blocked"].status, "blocked")
            self.assertFalse((finalized_run / "run_summary.json").exists())
            self.assertTrue((finalized_run / "run_summary.md").exists())
            self.assertTrue((recent_run / "run_summary.json").exists())
            self.assertTrue((blocked_run / "run_summary.json").exists())
            self.assertTrue((root / "archive/runtime_cleanup_report.md").exists())

    def test_runtime_json_cleanup_blocks_pending_memory_drafts_and_missing_final_reports(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            pending_run = seed_finalized_run(root, "2026-04-01_pending-memory")
            (pending_run / "memory_update_drafts.json").write_text(
                '{"items": [{"proposal_id": "proposal-1", "status": "ready"}]}',
                encoding="utf-8",
            )
            synthesis_run = seed_finalized_run(root, "2026-04-01_missing-final-report")
            synthesis_dir = synthesis_run / "reports/human_synthesis"
            synthesis_dir.mkdir(parents=True)
            (synthesis_dir / "TEST_synthesis_pack.md").write_text("# Synthesis Pack\n", encoding="utf-8")

            result = cleanup_runtime_json(
                root=root,
                current_date=date(2026, 5, 24),
                retention_days=7,
            )

            by_run = {run.run_id: run for run in result.runs}
            self.assertEqual(by_run["2026-04-01_pending-memory"].status, "blocked")
            self.assertIn("proposal-1", by_run["2026-04-01_pending-memory"].blocked_paths)
            self.assertEqual(by_run["2026-04-01_missing-final-report"].status, "blocked")
            self.assertIn(
                "agents/runs/2026-04-01_missing-final-report/reports/human_synthesis/TEST_final_human_report.md",
                by_run["2026-04-01_missing-final-report"].blocked_paths,
            )

    def test_runtime_json_cleanup_accepts_required_markdown_already_archived(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            run_id = "2026-04-01_archived-core"
            run_dir = seed_finalized_run(root, run_id)
            archive_dir = root / "archive" / "runs" / "2026" / run_id
            archive_dir.mkdir(parents=True)
            for name in ("run_summary.md", "quality_report.md"):
                (run_dir / name).rename(archive_dir / name)

            result = cleanup_runtime_json(
                root=root,
                current_date=date(2026, 5, 24),
                retention_days=0,
                write=True,
            )

            by_run = {run.run_id: run for run in result.runs}
            self.assertEqual(by_run[run_id].status, "deleted")
            self.assertFalse((run_dir / "run_summary.json").exists())
            self.assertTrue((archive_dir / "run_summary.md").exists())


def seed_repo(root: Path) -> Path:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking/current_holdings").mkdir(parents=True)
    (root / "stock_tracking/monitoring").mkdir(parents=True)
    (root / "stock_tracking/rejected").mkdir(parents=True)
    (root / "agents").mkdir(parents=True)
    (root / "docs/plans").mkdir(parents=True)
    (root / "strategy").mkdir(parents=True)
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
    (root / "agents/human_review_queue.md").write_text(
        "\n".join(
            [
                "# Human Review Queue",
                "",
                "| ID | Type | Status | Decision Needed | Evidence |",
                "| --- | --- | --- | --- | --- |",
                "| HRQ-1 | candidate_verification | open | decide | agents/runs/2026-04-01_weekly/market_research/candidate_review.md |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    run_dir = root / "agents/runs/2026-04-01_weekly"
    (run_dir / "reports/opportunity_assessment").mkdir(parents=True)
    (run_dir / "market_research").mkdir(parents=True)
    (run_dir / "reports/opportunity_assessment/AMZN_opportunity_assessment.md").write_text("# AMZN\n", encoding="utf-8")
    (run_dir / "reports/opportunity_assessment/OLD_opportunity_assessment.md").write_text("# OLD\n", encoding="utf-8")
    (run_dir / "market_research/candidate_review.md").write_text("# Candidate Review\n", encoding="utf-8")
    return root


def seed_finalized_run(root: Path, run_id: str) -> Path:
    run_dir = root / "agents" / "runs" / run_id
    run_dir.mkdir(parents=True)
    for name in ("run_summary", "quality_report", "memory_reflection", "finalization", "final_digest"):
        (run_dir / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")
        (run_dir / f"{name}.json").write_text('{"ok": true}\n', encoding="utf-8")
    (run_dir / "memory_update_drafts.json").write_text('{"items": []}\n', encoding="utf-8")
    (run_dir / "memory_update_drafts.md").write_text("# Memory Update Drafts\n\n- No memory update proposals.\n", encoding="utf-8")
    (run_dir / "raw/provider").mkdir(parents=True)
    (run_dir / "raw/provider/raw_payload.json").write_text('{"raw": true}\n', encoding="utf-8")
    return run_dir


def write_stock_csv(path: Path, rows: list[str]) -> None:
    header = "ticker,company_name,exchange,country,sector,industry,status,stock_info_file"
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
