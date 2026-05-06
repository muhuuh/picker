from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.evidence import Source, new_packet, write_packet
from stock_research.memory_reflection import (
    build_recurring_failure_report,
    build_run_reflection,
    write_recurring_failure_report,
    write_run_reflection,
)
from stock_research.run_finalization import finalize_run


class MemoryReflectionTests(unittest.TestCase):
    def test_reflection_detects_missing_summary_and_unmatched_provider_task(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_run_repo(Path(temp_dir))
            run_dir = root / "agents/runs/2026-05-09_weekly"
            manifest = {
                "provider_tasks": [
                    {
                        "id": "exa_theme_grid",
                        "provider": "exa",
                        "subject_id": "grid",
                    }
                ],
                "analysis_tasks": [],
            }
            (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

            reflection = build_run_reflection(root, "2026-05-09_weekly", date(2026, 5, 4))

            self.assertEqual(reflection.metrics["provider_tasks_planned"], 1)
            self.assertEqual(reflection.metrics["evidence_packets"], 0)
            self.assertTrue(any(issue.category == "missing_run_summary" for issue in reflection.issues))
            self.assertTrue(any(issue.category == "planned_provider_task_without_packet" for issue in reflection.issues))
            self.assertTrue(reflection.memory_update_proposals)

    def test_reflection_counts_valid_packets_and_writes_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_run_repo(Path(temp_dir))
            run_dir = root / "agents/runs/2026-05-09_weekly"
            (run_dir / "manifest.json").write_text(json.dumps({"provider_tasks": [], "analysis_tasks": []}), encoding="utf-8")
            (run_dir / "run_summary.md").write_text("# Summary\n", encoding="utf-8")
            (run_dir / "quality_report.md").write_text("# Quality\n", encoding="utf-8")
            packet = new_packet(
                provider="exa",
                subject_type="theme",
                subject_id="grid",
                time_window="latest",
                current_date=date(2026, 5, 4),
                sources=[
                    Source(
                        source_id="src1",
                        provider="exa",
                        source_type="web",
                        title="Grid source",
                        artifact_path="agents/runs/2026-05-09_weekly/raw/exa/grid.json",
                    )
                ],
            )
            write_packet(packet, run_dir / "evidence_packets" / "packet.json")

            reflection = build_run_reflection(root, "2026-05-09_weekly", date(2026, 5, 4))
            json_path, md_path = write_run_reflection(root, reflection)

            self.assertEqual(reflection.metrics["valid_evidence_packets"], 1)
            self.assertEqual(reflection.metrics["issues"], 0)
            self.assertFalse(reflection.memory_update_proposals)
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())
            self.assertIn("Memory Reflection", md_path.read_text(encoding="utf-8"))

    def test_recurring_failure_report_detects_repeated_issue_category(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_run_repo(Path(temp_dir))
            write_reflection_json(root, "2026-05-09_weekly", "missing_quality_report")
            write_reflection_json(root, "2026-05-16_weekly", "missing_quality_report")

            report = build_recurring_failure_report(root, threshold=2, current_date=date(2026, 5, 17))
            json_path, md_path = write_recurring_failure_report(root, report)

            self.assertEqual(report.runs_scanned, 2)
            self.assertEqual(len(report.patterns), 1)
            self.assertEqual(report.patterns[0].category, "missing_quality_report")
            self.assertTrue(report.memory_update_proposals)
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

    def test_recurring_failure_report_respects_threshold(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_run_repo(Path(temp_dir))
            write_reflection_json(root, "2026-05-09_weekly", "missing_quality_report")

            report = build_recurring_failure_report(root, threshold=2, current_date=date(2026, 5, 17))

            self.assertEqual(report.runs_scanned, 1)
            self.assertFalse(report.patterns)
            self.assertFalse(report.memory_update_proposals)

    def test_finalize_run_writes_learning_loop_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_run_repo(Path(temp_dir))
            run_dir = root / "agents/runs/2026-05-09_weekly"
            (run_dir / "manifest.json").write_text(json.dumps({"provider_tasks": [], "analysis_tasks": []}), encoding="utf-8")
            (run_dir / "run_summary.md").write_text("# Summary\n", encoding="utf-8")
            (run_dir / "quality_report.md").write_text("# Quality\n", encoding="utf-8")

            finalization, paths = finalize_run(root, "2026-05-09_weekly", date(2026, 5, 17))

            self.assertEqual(finalization.status, "complete")
            self.assertEqual(finalization.metrics["reflection_issues"], 0)
            self.assertTrue((run_dir / "memory_reflection.json").exists())
            self.assertTrue((root / "agents/memory/recurring_failures.json").exists())
            self.assertTrue((run_dir / "memory_update_drafts.json").exists())
            self.assertTrue((run_dir / "memory_update_drafts.md").exists())
            self.assertTrue((run_dir / "finalization.json").exists())
            self.assertTrue((run_dir / "finalization.md").exists())
            self.assertEqual(finalization.metrics["memory_update_drafts"], 0)
            self.assertEqual(len(paths), 2)


def seed_run_repo(root: Path) -> Path:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking").mkdir(parents=True)
    (root / "agents/runs/2026-05-09_weekly/evidence_packets").mkdir(parents=True)
    return root


def write_reflection_json(root: Path, run_id: str, category: str) -> None:
    run_dir = root / "agents" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "memory_reflection.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "run_dir": f"agents/runs/{run_id}",
                "generated_at": "2026-05-17",
                "metrics": {"issues": 1},
                "issues": [
                    {
                        "severity": "medium",
                        "category": category,
                        "summary": f"{category} happened.",
                        "evidence": f"agents/runs/{run_id}/quality_report.md",
                    }
                ],
                "memory_update_proposals": [],
            }
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
