from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.codex_review_pack import build_codex_review_pack


class CodexReviewPackTests(unittest.TestCase):
    def test_open_human_review_items_are_not_pack_quality_failures(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_id = "2026-05-16_weekly"
            seed_required_pack_artifacts(root, run_id)
            (root / "agents/human_review_digest.md").write_text(
                "# Human Review Digest\n\nStatus: needs_user_review\n\nOpen items summarized: 1\n",
                encoding="utf-8",
            )
            (root / "agents/human_review_queue.md").write_text("# Human Review Queue\n", encoding="utf-8")

            pack = build_codex_review_pack(root, run_id)

            self.assertEqual(pack.status, "ready")
            self.assertEqual(pack.quality_findings, [])
            self.assertEqual(
                pack.final_human_report_targets[0]["path"],
                "agents/runs/2026-05-16_weekly/reports/human_synthesis/AAPL_final_human_report.md",
            )
            self.assertEqual(
                pack.post_codex_quality_command,
                "python -m stock_research quality-report --run-id 2026-05-16_weekly --write --require-final-reports",
            )
            self.assertTrue(any("--require-final-reports" in instruction for instruction in pack.codex_instructions))
            self.assertTrue(any("recurring_coverage" in instruction for instruction in pack.codex_instructions))
            self.assertEqual(pack.required_artifacts[0]["path"], f"agents/runs/{run_id}/manifest.json")


def seed_required_pack_artifacts(root: Path, run_id: str) -> None:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking").mkdir()
    run_dir = root / "agents" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text('{"recurring_coverage": {}}\n', encoding="utf-8")
    for filename in ("quality_report.md", "run_summary.md", "finalization.md", "memory_reflection.md"):
        (run_dir / filename).write_text("# ok\n", encoding="utf-8")
    (run_dir / "final_digest.json").write_text('{"ticker_count": 1, "quality_findings": []}\n', encoding="utf-8")
    (run_dir / "final_digest.md").write_text("# Final Digest\n", encoding="utf-8")
    report_dir = run_dir / "reports" / "opportunity_assessment"
    report_dir.mkdir(parents=True)
    (report_dir / "AAPL_opportunity_assessment.md").write_text("# AAPL\n", encoding="utf-8")
    synthesis_dir = run_dir / "reports" / "human_synthesis"
    synthesis_dir.mkdir(parents=True)
    (synthesis_dir / "AAPL_synthesis_pack.md").write_text("# AAPL Synthesis Pack\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
