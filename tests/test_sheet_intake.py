from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from stock_research.cli import main
from stock_research.sheet_intake import (
    build_sheet_intake_candidate_review,
    normalize_sheet_rows,
)


class SheetIntakeTests(unittest.TestCase):
    def test_normalizes_sheet_row_dicts_and_selects_research_action(self):
        rows = normalize_sheet_rows(
            [
                {
                    "__row_number": "5",
                    "Date": "2026-05-17",
                    "Name": "Robo Holdings",
                    "Ticker": "$robo",
                    "Mcap": "1B",
                    "Forward PE": "22",
                    "P/S": "4.5",
                    "Forecast": "+15%",
                    "Score": "b+",
                    "available": "Yes",
                    "action": "research",
                    "Comment": "Robotics supplier worth checking.",
                    "Source / link": "https://example.com/robo",
                }
            ]
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].row_number, 5)
        self.assertEqual(rows[0].ticker, "ROBO")
        self.assertEqual(rows[0].score, "B+")
        self.assertEqual(rows[0].price_to_sales, "4.5")
        self.assertEqual(rows[0].available, "yes")
        self.assertEqual(rows[0].action, "research")

    def test_sheet_intake_writes_candidate_review_and_queue(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_repo(root)
            result = build_sheet_intake_candidate_review(
                root=root,
                rows=[
                    {
                        "__row_number": 2,
                        "Name": "Robo Holdings",
                        "Ticker": "ROBO",
                        "Industry": "Robotics",
                        "Score": "A",
                        "available": "yes",
                        "action": "research",
                        "Comment": "Robotics supplier worth checking.",
                    },
                    {
                        "__row_number": 3,
                        "Name": "Skip Co",
                        "Ticker": "SKIP",
                        "action": "",
                    },
                ],
                current_date=date(2026, 5, 17),
                write=True,
                queue_review=True,
            )
            market_dir = root / "agents" / "runs" / "2026-05-17_sheet-intake" / "market_research"
            leads = json.loads((market_dir / "sheet_intake_candidate_leads.json").read_text(encoding="utf-8"))
            review = (market_dir / "candidate_review.md").read_text(encoding="utf-8")
            queue = (root / "agents" / "human_review_queue.md").read_text(encoding="utf-8")

        self.assertEqual(result.status, "ready_for_human_review")
        self.assertEqual(result.selected_count, 1)
        self.assertEqual(result.skipped_count, 1)
        self.assertEqual(leads[0]["ticker"], "ROBO")
        self.assertEqual(leads[0]["source_channels"], ["sheet"])
        self.assertEqual(leads[0]["verification_status"], "unverified")
        self.assertIn("Robo Holdings (ROBO)", review)
        self.assertIn("candidate_review.md#CRG-0001", queue)
        self.assertIn("| HRQ-0001 |", queue)

    def test_sheet_intake_can_approve_verification_and_write_plan(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_repo(root)
            result = build_sheet_intake_candidate_review(
                root=root,
                rows=[
                    {
                        "__row_number": 2,
                        "Name": "Robo Holdings",
                        "Ticker": "ROBO",
                        "available": "yes",
                        "action": "research",
                        "Comment": "Robotics supplier worth checking.",
                    }
                ],
                current_date=date(2026, 5, 17),
                write=True,
                queue_review=True,
                approve_verification=True,
                write_verification_plan=True,
            )
            run_dir = root / "agents" / "runs" / "2026-05-17_sheet-intake" / "market_research"
            queue = (root / "agents" / "human_review_queue.md").read_text(encoding="utf-8")
            manifest = json.loads((run_dir / "candidate_verification_manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(result.status, "ready_for_verification")
        self.assertEqual(result.review_ids, ["HRQ-0001"])
        self.assertIn("| HRQ-0001 | 2026-05-17 | Review discovery candidate Robo Holdings", queue)
        self.assertIn("| approved |", queue)
        self.assertTrue(any(task["subject_id"] == "ROBO" for task in manifest["provider_tasks"]))
        self.assertTrue(any(task["subject_id"] == "ROBO" for task in manifest["analysis_tasks"]))

    def test_sheet_intake_cli_accepts_rows_from_stdin(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_repo(root)
            rows_json = json.dumps(
                [
                    {
                        "__row_number": 2,
                        "Name": "Robo Holdings",
                        "Ticker": "ROBO",
                        "available": "yes",
                        "action": "research",
                    }
                ]
            )
            buffer = io.StringIO()
            with patch("sys.stdin", io.StringIO(rows_json)), redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--root",
                        str(root),
                        "sheet-intake",
                        "selected-rows",
                        "--rows-json",
                        "-",
                        "--write",
                        "--queue-review",
                        "--today",
                        "2026-05-17",
                    ]
                )
            payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["selected_count"], 1)
        self.assertEqual(payload["review_ids"], ["HRQ-0001"])


def write_minimal_repo(root: Path) -> None:
    (root / "AGENTS.md").write_text("# Test agents\n", encoding="utf-8")
    (root / "MEMORY.md").write_text("# Memory\n", encoding="utf-8")
    (root / "stock_tracking" / "current_holdings").mkdir(parents=True, exist_ok=True)
    (root / "stock_tracking" / "monitoring").mkdir(parents=True, exist_ok=True)
    (root / "stock_tracking" / "rejected").mkdir(parents=True, exist_ok=True)
    (root / "stock_tracking" / "current_holdings" / "current_holdings.csv").write_text(
        "ticker,company_name,status\n",
        encoding="utf-8",
    )
    (root / "stock_tracking" / "monitoring" / "monitoring.csv").write_text(
        "ticker,company_name,status\n",
        encoding="utf-8",
    )
    (root / "stock_tracking" / "rejected" / "rejected.csv").write_text(
        "ticker,company_name,next_eligible_review_date\n",
        encoding="utf-8",
    )
    memory_dir = root / "agents" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "README.md",
        "memory_index.md",
        "orchestrator_lessons.md",
        "source_quality.md",
        "specialist_playbooks.md",
        "evaluation_metrics.md",
        "deprecated_memory.md",
    ):
        (memory_dir / name).write_text("# Test memory\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
