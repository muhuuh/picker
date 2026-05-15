from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.run_end_review import build_run_end_review_summary


class RunEndReviewTests(unittest.TestCase):
    def test_writes_digest_and_run_local_summary(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))

            summary = build_run_end_review_summary(
                root=root,
                run_id="manual_run",
                current_date=date(2026, 5, 16),
                write=True,
            )

            self.assertEqual(summary.open_item_count, 1)
            self.assertIn("agents/human_review_digest.md", summary.written_paths)
            self.assertIn("agents/runs/manual_run/human_review_digest_summary.md", summary.written_paths)
            text = (root / "agents/runs/manual_run/human_review_digest_summary.md").read_text(encoding="utf-8")
            self.assertIn("Allowed decisions are approve, reject, needs more research, or leave open.", text)


def seed_repo(root: Path) -> Path:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking").mkdir(parents=True)
    (root / "agents/runs/manual_run").mkdir(parents=True)
    (root / "agents/human_review_queue.md").write_text(
        "\n".join(
            [
                "# Human Review Queue",
                "",
                "| ID | Date Added | Item | Decision Needed | Priority | Status | Related Files | Evidence / Run Link | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| HRQ-0001 | 2026-05-16 | Review Grok/X lead. | Approve verification or reject. | high | open | agents/runs/manual_run/market_research | agents/runs/manual_run/market_research/candidate_review.md#CRG-0001 | Candidate surfaced from grok with verification=grok_only. |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return root


if __name__ == "__main__":
    unittest.main()
