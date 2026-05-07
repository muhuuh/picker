from __future__ import annotations

from datetime import date
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from contextlib import redirect_stdout

from stock_research.agent_runtime.proposal_review import build_proposal_review
from stock_research.cli import main
from stock_research.repo import load_first_table


class AgentRuntimeProposalReviewTests(unittest.TestCase):
    def test_build_proposal_review_writes_report_and_queues_review_items_idempotently(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            write_runtime_output(root)

            result = build_proposal_review(
                root=root,
                run_id="test_weekly",
                current_date=date(2026, 5, 7),
                write=True,
                queue_review=True,
            )
            second_result = build_proposal_review(
                root=root,
                run_id="test_weekly",
                current_date=date(2026, 5, 7),
                write=True,
                queue_review=True,
            )

            self.assertEqual(result.status, "ready_for_human_review")
            self.assertEqual(len(result.proposals), 1)
            self.assertTrue((root / "agents/runs/test_weekly/orchestrator_update_proposals.md").exists())
            rows = load_first_table(root / "agents/human_review_queue.md")
            proposal_rows = [row for row in rows if "ORP-0001" in row.get("Evidence / Run Link", "")]
            self.assertEqual(len(proposal_rows), 1)
            self.assertIn("agents/human_review_queue.md", second_result.written_paths)

    def test_cli_queue_proposals(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            write_runtime_output(root)

            with redirect_stdout(io.StringIO()):
                exit_code = main(
                    [
                        "--root",
                        str(root),
                        "agent-runtime",
                        "queue-proposals",
                        "--run-id",
                        "test_weekly",
                        "--write",
                        "--queue-review",
                        "--today",
                        "2026-05-07",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue((root / "agents/runs/test_weekly/orchestrator_update_proposals.md").exists())


def seed_repo(root: Path) -> Path:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking/stock_info_files/monitoring").mkdir(parents=True)
    (root / "agents/runs/test_weekly/reports/company_news_specialist").mkdir(parents=True)
    (root / "agents/memory").mkdir(parents=True)
    (root / "agents/human_review_queue.md").write_text(
        "\n".join(
            [
                "# Human Review Queue",
                "",
                "## Review Items",
                "",
                "| ID | Date Added | Item | Decision Needed | Priority | Status | Related Files | Evidence / Run Link | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "agents/memory/orchestrator_lessons.md").write_text(
        "\n".join(
            [
                "# Orchestrator Lessons",
                "",
                "- id: orch-test",
                "- date: 2026-05-07",
                "- type: procedural",
                "- scope: orchestrator",
                "- status: active",
                "- confidence: high",
                "- trigger/source: test",
                "- lesson: Test lesson.",
                "- use_when: Testing.",
                "- do_not_use_when: Never.",
                "- evidence: `tests/test_agent_runtime_proposal_review.py`",
                "- owner: tests",
                "- next_review: 2026-06-01",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "stock_tracking/stock_info_files/monitoring/AAPL.md").write_text("# AAPL\n", encoding="utf-8")
    (root / "agents/runs/test_weekly/reports/company_news_specialist/AAPL_company_news_review.md").write_text(
        "# AAPL Company News Review\n",
        encoding="utf-8",
    )
    return root


def write_runtime_output(root: Path) -> None:
    output = {
        "agent_id": "main_orchestrator",
        "run_id": "test_weekly",
        "status": "ready",
        "summary": "This SDK output is long enough to be reviewable and proposes a source-backed company-file update for testing.",
        "memory_item_ids_used": ["orch-test"],
        "specialist_results": [
            {
                "agent_id": "company_news_specialist",
                "subject_type": "company",
                "subject_id": "AAPL",
                "status": "ready",
                "summary": "Specialist summary.",
                "memory_item_ids_used": ["orch-test"],
                "sources": [
                    {
                        "source_id": "source-1",
                        "title": "AAPL company news review",
                        "artifact_path": "reports/company_news_specialist/AAPL_company_news_review.md",
                        "confidence": "high",
                    }
                ],
            }
        ],
        "file_update_proposals": [
            {
                "target_file": "stock_tracking/stock_info_files/monitoring/AAPL.md",
                "update_type": "company_file_update",
                "summary": "Update AAPL developments section from the latest reviewed company-news evidence.",
                "confidence": "high",
                "source_ids": ["source-1"],
                "needs_human_review": False,
            }
        ],
    }
    (root / "agents/runs/test_weekly/agent_runtime_main_orchestrator.json").write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
