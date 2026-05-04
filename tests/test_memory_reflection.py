from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.evidence import Source, new_packet, write_packet
from stock_research.memory_reflection import build_run_reflection, write_run_reflection


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


def seed_run_repo(root: Path) -> Path:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking").mkdir(parents=True)
    (root / "agents/runs/2026-05-09_weekly/evidence_packets").mkdir(parents=True)
    return root


if __name__ == "__main__":
    unittest.main()
