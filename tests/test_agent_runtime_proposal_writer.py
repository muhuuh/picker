from __future__ import annotations

from contextlib import redirect_stdout
from datetime import date
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.agent_runtime.proposal_writer import apply_approved_proposal
from stock_research.cli import main


class AgentRuntimeProposalWriterTests(unittest.TestCase):
    def test_open_review_item_blocks_application(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir), review_status="open")

            result = apply_approved_proposal(
                root=root,
                run_id="test_weekly",
                proposal_id="ORP-0001",
                current_date=date(2026, 5, 7),
                write=True,
            )

            self.assertEqual(result.status, "blocked")
            self.assertIn("not 'approved'", result.findings[0])
            self.assertNotIn("ORP-0001", (root / "stock_tracking/stock_info_files/monitoring/AAPL.md").read_text(encoding="utf-8"))

    def test_approved_dry_run_reports_plan_without_writing(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir), review_status="approved")

            result = apply_approved_proposal(
                root=root,
                run_id="test_weekly",
                proposal_id="ORP-0001",
                current_date=date(2026, 5, 7),
            )

            self.assertEqual(result.status, "ready_to_apply")
            self.assertIn("append Developments row", result.planned_changes)
            self.assertEqual(result.written_paths, [])
            self.assertNotIn("ORP-0001", (root / "stock_tracking/stock_info_files/monitoring/AAPL.md").read_text(encoding="utf-8"))

    def test_approved_write_updates_company_file_and_is_idempotent(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir), review_status="approved")

            result = apply_approved_proposal(
                root=root,
                run_id="test_weekly",
                proposal_id="ORP-0001",
                current_date=date(2026, 5, 7),
                write=True,
            )
            second_result = apply_approved_proposal(
                root=root,
                run_id="test_weekly",
                proposal_id="ORP-0001",
                current_date=date(2026, 5, 7),
                write=True,
            )

            company_text = (root / "stock_tracking/stock_info_files/monitoring/AAPL.md").read_text(encoding="utf-8")
            self.assertEqual(result.status, "applied")
            self.assertEqual(second_result.status, "already_applied")
            self.assertIn("Last updated: 2026-05-07", company_text)
            self.assertEqual(company_text.count("Applied ORP-0001"), 1)
            self.assertEqual(company_text.count("SDK approved proposal ORP-0001"), 1)
            self.assertTrue((root / "agents/runs/test_weekly/applied_update_proposals.md").exists())

    def test_invalid_target_blocks_application(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir), review_status="approved", target_file="README.md")

            result = apply_approved_proposal(
                root=root,
                run_id="test_weekly",
                proposal_id="ORP-0001",
                current_date=date(2026, 5, 7),
                write=True,
            )

            self.assertEqual(result.status, "blocked")
            self.assertIn("outside stock_info_files", result.findings[0])

    def test_cli_apply_proposal(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir), review_status="approved")

            with redirect_stdout(io.StringIO()):
                exit_code = main(
                    [
                        "--root",
                        str(root),
                        "agent-runtime",
                        "apply-proposal",
                        "--run-id",
                        "test_weekly",
                        "--proposal-id",
                        "ORP-0001",
                        "--write",
                        "--today",
                        "2026-05-07",
                    ]
                )

            self.assertEqual(exit_code, 0)
            company_text = (root / "stock_tracking/stock_info_files/monitoring/AAPL.md").read_text(encoding="utf-8")
            self.assertIn("Applied ORP-0001", company_text)


def seed_repo(root: Path, *, review_status: str, target_file: str = "stock_tracking/stock_info_files/monitoring/AAPL.md") -> Path:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking/stock_info_files/monitoring").mkdir(parents=True)
    (root / "agents/runs/test_weekly").mkdir(parents=True)
    (root / "agents/human_review_queue.md").write_text(
        "\n".join(
            [
                "# Human Review Queue",
                "",
                "## Review Items",
                "",
                "| ID | Date Added | Item | Decision Needed | Priority | Status | Related Files | Evidence / Run Link | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                f"| HRQ-0001 | 2026-05-07 | Review proposal. | Approve before writing. | medium | {review_status} | {target_file} | agents/runs/test_weekly/orchestrator_update_proposals.md#ORP-0001 | Test proposal. |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "agents/runs/test_weekly/orchestrator_update_proposals.md").write_text(
        "\n".join(
            [
                "# Orchestrator Update Proposals: test_weekly",
                "",
                "## File Update Proposals",
                "",
                "| Proposal ID | Target File | Update Type | Confidence | Needs Human Review | Source IDs | Summary |",
                "| --- | --- | --- | --- | --- | --- | --- |",
                f"| ORP-0001 | {target_file} | company_news_developments | high | no | source-1 | Update AAPL developments from approved proposal. |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "stock_tracking/stock_info_files/monitoring/AAPL.md").write_text(
        "\n".join(
            [
                "# AAPL Apple Inc.",
                "",
                "Last updated: 2026-05-04",
                "",
                "## Developments",
                "",
                "| Date | Development | Source | Impact | Confidence |",
                "| --- | --- | --- | --- | --- |",
                "",
                "## Source Log",
                "",
                "| Date accessed | Source | URL / artifact | Notes |",
                "| --- | --- | --- | --- |",
                "",
                "## Change Log",
                "",
                "| Date | Updated by | Summary | Sources |",
                "| --- | --- | --- | --- |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return root


if __name__ == "__main__":
    unittest.main()
