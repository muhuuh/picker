from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from stock_research.cli import main
from stock_research.human_review_digest import build_human_review_digest, format_human_review_digest


class HumanReviewDigestTests(unittest.TestCase):
    def test_digest_groups_only_open_items(self):
        with TemporaryDirectory() as temp_dir:
            root = write_review_digest_scaffold(Path(temp_dir))

            digest = build_human_review_digest(root=root, current_date=date(2026, 5, 11))
            markdown = format_human_review_digest(digest)

        self.assertEqual(digest.status, "needs_user_review")
        self.assertEqual(digest.open_item_count, 3)
        self.assertEqual(digest.category_counts["company_file_update"], 1)
        self.assertEqual(digest.category_counts["candidate_verification_grok"], 1)
        self.assertEqual(digest.category_counts["candidate_verification"], 1)
        self.assertIn("Company File Updates / FYI", markdown)
        self.assertIn("Grok/X Candidate Verification", markdown)
        self.assertIn("Approve follow-up verification, reject/ignore, or leave open. Do not promote yet.", markdown)
        self.assertNotIn("HRQ-0004", markdown)

    def test_digest_separates_verified_monitoring_candidates_from_grok_verification(self):
        with TemporaryDirectory() as temp_dir:
            root = write_review_digest_scaffold(Path(temp_dir))
            queue = root / "agents" / "human_review_queue.md"
            queue.write_text(
                queue.read_text(encoding="utf-8").replace(
                    "| HRQ-0004 |",
                    "| HRQ-0005 | 2026-05-12 | Review verified discovery candidate Amkor Technology, Inc. (AMKR) for possible monitoring. | Approve adding this candidate to monitoring, or request more research first. | medium | open | agents/runs/2026-05-12_manual-market/market_research | agents/runs/2026-05-12_manual-market/market_research/candidate_review.md#CRG-0001 | Candidate surfaced from exa, grok with verification=verified, hype=unknown, cooldown=not_rejected. Tickers: AMKR. Source IDs: exa_result_1, xai_x_source_1. |\n| HRQ-0004 |",
                ),
                encoding="utf-8",
            )

            digest = build_human_review_digest(root=root, current_date=date(2026, 5, 11))
            markdown = format_human_review_digest(digest)

        self.assertEqual(digest.category_counts["candidate_monitoring_review"], 1)
        self.assertEqual(digest.category_counts["candidate_verification_grok"], 1)
        self.assertIn("Monitoring Candidate Reviews", markdown)
        self.assertIn("Approve adding to monitoring, request more research, or reject/ignore.", markdown)

    def test_digest_keeps_newest_duplicate_candidate_row(self):
        with TemporaryDirectory() as temp_dir:
            root = write_review_digest_scaffold(Path(temp_dir))
            queue = root / "agents" / "human_review_queue.md"
            queue.write_text(
                queue.read_text(encoding="utf-8").replace(
                    "| HRQ-0004 |",
                    "| HRQ-0005 | 2026-05-12 | Review verified discovery candidate Amkor Technology, Inc. (AMKR) for possible monitoring. | Approve adding this candidate to monitoring, or request more research first. | medium | open | agents/runs/old/market_research | agents/runs/old/market_research/candidate_review.md#CRG-0001 | Candidate surfaced from exa, grok with verification=verified, hype=unknown, cooldown=not_rejected. Tickers: AMKR. |\n"
                    "| HRQ-0006 | 2026-05-14 | Review verified discovery candidate Amkor Technology, Inc. (AMKR) for possible monitoring. | Approve adding this candidate to monitoring, or request more research first. | medium | open | agents/runs/new/market_research | agents/runs/new/market_research/candidate_review.md#CRG-0001 | Candidate surfaced from exa, grok with verification=verified, hype=unknown, cooldown=not_rejected. Tickers: AMKR. |\n"
                    "| HRQ-0004 |",
                ),
                encoding="utf-8",
            )

            digest = build_human_review_digest(root=root, current_date=date(2026, 5, 15))
            markdown = format_human_review_digest(digest)

        self.assertEqual(digest.category_counts["candidate_monitoring_review"], 1)
        self.assertIn("HRQ-0006", markdown)
        self.assertNotIn("HRQ-0005", markdown)

    def test_digest_write_creates_review_artifact(self):
        with TemporaryDirectory() as temp_dir:
            root = write_review_digest_scaffold(Path(temp_dir))

            digest = build_human_review_digest(root=root, current_date=date(2026, 5, 11), write=True)
            digest_path = root / "agents" / "human_review_digest.md"
            text = digest_path.read_text(encoding="utf-8")

        self.assertEqual(digest.written_paths, ["agents/human_review_digest.md"])
        self.assertIn("Open items summarized: 3", text)
        self.assertIn("Suggested Codex Prompt", text)

    def test_human_review_digest_cli_json(self):
        with TemporaryDirectory() as temp_dir:
            root = write_review_digest_scaffold(Path(temp_dir))
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--root",
                        str(root),
                        "human-review",
                        "digest",
                        "--format",
                        "json",
                        "--write",
                        "--today",
                        "2026-05-11",
                    ]
                )
            payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["open_item_count"], 3)
        self.assertIn("agents/human_review_digest.md", payload["written_paths"])


def write_review_digest_scaffold(root: Path) -> Path:
    (root / "AGENTS.md").write_text("# Test agents\n", encoding="utf-8")
    (root / "stock_tracking").mkdir(parents=True)
    (root / "agents").mkdir(parents=True)
    (root / "agents" / "human_review_queue.md").write_text(
        "\n".join(
            [
                "# Human Review Queue",
                "",
                "| ID | Date Added | Item | Decision Needed | Priority | Status | Related Files | Evidence / Run Link | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| HRQ-0001 | 2026-05-07 | Review SDK file update proposal ORP-0001 for stock_tracking/stock_info_files/monitoring/AAPL.md. | Approve, reject, or request more research before any company-file writer applies this update. | medium | open | stock_tracking/stock_info_files/monitoring/AAPL.md | agents/runs/2026-05-09_weekly/orchestrator_update_proposals.md#ORP-0001 | Update AAPL company news from source-validated evidence. |",
                "| HRQ-0002 | 2026-05-10 | Review Grok/X discovery lead FLNC (FLNC) for follow-up verification. | Approve Exa/filing/financial verification of this Grok-only lead, or ignore it. | high | open | agents/runs/2026-05-10_manual-market/market_research | agents/runs/2026-05-10_manual-market/market_research/candidate_review.md#CRG-0001 | Candidate surfaced from grok with verification=grok_only, hype=high, cooldown=not_rejected. Tickers: FLNC. Source IDs: xai_x_source_1. |",
                "| HRQ-0003 | 2026-05-10 | Review discovery candidate ADS-TEC Energy (ADSE) for verification before monitoring. | Approve follow-up company and financial verification before considering monitoring. | medium | open | agents/runs/2026-05-10_manual-market/market_research | agents/runs/2026-05-10_manual-market/market_research/candidate_review.md#CRG-0002 | Candidate surfaced from exa with verification=exa_only, hype=unknown, cooldown=not_rejected. Tickers: ADSE. Source IDs: exa_result_1. |",
                "| HRQ-0004 | 2026-05-10 | Approved old item | No longer open. | low | approved |  |  |  |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return root


if __name__ == "__main__":
    unittest.main()
