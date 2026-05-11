from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from stock_research.cli import main
from stock_research.human_review_decisions import (
    HumanReviewDecision,
    apply_human_review_decisions,
)


class HumanReviewDecisionTests(unittest.TestCase):
    def test_dry_run_reports_ready_without_changing_queue(self):
        with TemporaryDirectory() as temp_dir:
            root = write_review_decision_scaffold(Path(temp_dir))
            queue_path = root / "agents" / "human_review_queue.md"
            before = queue_path.read_text(encoding="utf-8")

            result = apply_human_review_decisions(
                root=root,
                decisions=[HumanReviewDecision(review_id="HRQ-0002", status="approved", note="Verify this lead.")],
                current_date=date(2026, 5, 11),
            )
            after = queue_path.read_text(encoding="utf-8")

        self.assertEqual(result.status, "ready_to_apply")
        self.assertEqual(result.applied_count, 0)
        self.assertEqual(result.blocked_count, 0)
        self.assertEqual(before, after)

    def test_write_updates_queue_and_refreshes_digest(self):
        with TemporaryDirectory() as temp_dir:
            root = write_review_decision_scaffold(Path(temp_dir))

            result = apply_human_review_decisions(
                root=root,
                decisions=[HumanReviewDecision(review_id="HRQ-0002", status="approved", note="Run verification next.")],
                current_date=date(2026, 5, 11),
                write=True,
            )
            queue_text = (root / "agents" / "human_review_queue.md").read_text(encoding="utf-8")
            digest_text = (root / "agents" / "human_review_digest.md").read_text(encoding="utf-8")

        self.assertEqual(result.status, "applied")
        self.assertEqual(result.applied_count, 1)
        self.assertEqual(result.written_paths, ["agents/human_review_queue.md", "agents/human_review_digest.md"])
        self.assertIn("| HRQ-0002 | 2026-05-10 | Review Grok/X discovery lead FLNC", queue_text)
        self.assertIn("| medium | approved |", queue_text)
        self.assertIn("Decision update 2026-05-11 by user: approved. Run verification next.", queue_text)
        self.assertNotIn("HRQ-0002", digest_text)
        self.assertIn("Open items summarized: 1", digest_text)

    def test_unknown_review_id_blocks_all_writes(self):
        with TemporaryDirectory() as temp_dir:
            root = write_review_decision_scaffold(Path(temp_dir))
            queue_path = root / "agents" / "human_review_queue.md"
            before = queue_path.read_text(encoding="utf-8")

            result = apply_human_review_decisions(
                root=root,
                decisions=[
                    HumanReviewDecision(review_id="HRQ-0002", status="approved"),
                    HumanReviewDecision(review_id="HRQ-9999", status="rejected"),
                ],
                current_date=date(2026, 5, 11),
                write=True,
            )
            after = queue_path.read_text(encoding="utf-8")

        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.applied_count, 0)
        self.assertEqual(before, after)
        self.assertTrue(any("No human-review row found" in finding for item in result.items for finding in item.findings))

    def test_invalid_status_blocks(self):
        with TemporaryDirectory() as temp_dir:
            root = write_review_decision_scaffold(Path(temp_dir))

            result = apply_human_review_decisions(
                root=root,
                decisions=[HumanReviewDecision(review_id="HRQ-0002", status="maybe")],
                current_date=date(2026, 5, 11),
                write=True,
            )

        self.assertEqual(result.status, "blocked")
        self.assertIn("Invalid status", result.items[0].findings[0])

    def test_cli_decide_write(self):
        with TemporaryDirectory() as temp_dir:
            root = write_review_decision_scaffold(Path(temp_dir))
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--root",
                        str(root),
                        "human-review",
                        "decide",
                        "--set",
                        "HRQ-0002=needs_more_research",
                        "--note",
                        "Need financial check first.",
                        "--write",
                        "--today",
                        "2026-05-11",
                    ]
                )
            payload = json.loads(buffer.getvalue())
            queue_text = (root / "agents" / "human_review_queue.md").read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "applied")
        self.assertIn("| medium | needs_more_research |", queue_text)
        self.assertIn("Need financial check first.", queue_text)


def write_review_decision_scaffold(root: Path) -> Path:
    (root / "AGENTS.md").write_text("# Test agents\n", encoding="utf-8")
    (root / "stock_tracking").mkdir(parents=True)
    (root / "agents").mkdir(parents=True)
    (root / "agents" / "human_review_queue.md").write_text(
        "\n".join(
            [
                "# Human Review Queue",
                "",
                "Intro text stays untouched.",
                "",
                "| ID | Date Added | Item | Decision Needed | Priority | Status | Related Files | Evidence / Run Link | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| HRQ-0001 | 2026-05-07 | Review SDK file update proposal ORP-0001 for stock_tracking/stock_info_files/monitoring/AAPL.md. | Approve, reject, or request more research before any company-file writer applies this update. | medium | open | stock_tracking/stock_info_files/monitoring/AAPL.md | agents/runs/2026-05-09_weekly/orchestrator_update_proposals.md#ORP-0001 | Update AAPL company news from source-validated evidence. |",
                "| HRQ-0002 | 2026-05-10 | Review Grok/X discovery lead FLNC (FLNC) for follow-up verification. | Approve Exa/filing/financial verification of this Grok-only lead, or ignore it. | medium | open | agents/runs/2026-05-10_manual-market/market_research | agents/runs/2026-05-10_manual-market/market_research/candidate_review.md#CRG-0001 | Candidate surfaced from grok with verification=grok_only, hype=high, cooldown=not_rejected. Tickers: FLNC. Source IDs: xai_x_source_1. |",
                "",
                "Footer text stays untouched.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return root


if __name__ == "__main__":
    unittest.main()
