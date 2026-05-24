from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.artifact_hygiene import cleanup_runtime_json
from stock_research.knowledge_promotion import assess_knowledge_promotion


class KnowledgePromotionTests(unittest.TestCase):
    def test_complete_run_is_promoted_and_writes_status(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_promotion_repo(Path(temp_dir))

            result = assess_knowledge_promotion(
                root=root,
                run_id="2026-04-01_weekly",
                current_date=date(2026, 5, 24),
                write=True,
            )

            self.assertEqual(result.status, "promoted")
            self.assertTrue(result.cleanup_ready)
            self.assertEqual(result.blocker_count, 0)
            self.assertEqual(result.warning_count, 0)
            self.assertTrue((root / "agents/runs/2026-04-01_weekly/knowledge_promotion_status.md").exists())

    def test_missing_company_marker_blocks_promotion_and_json_cleanup(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_promotion_repo(Path(temp_dir))
            company_file = root / "stock_tracking/stock_info_files/monitoring/ABC.md"
            company_file.write_text("# ABC\n\nNo promoted run row yet.\n", encoding="utf-8")

            promotion = assess_knowledge_promotion(
                root=root,
                run_id="2026-04-01_weekly",
                current_date=date(2026, 5, 24),
            )
            cleanup = cleanup_runtime_json(
                root=root,
                current_date=date(2026, 5, 24),
                retention_days=0,
            )

            self.assertEqual(promotion.status, "blocked")
            self.assertFalse(promotion.cleanup_ready)
            self.assertTrue(any(finding.area == "company_files" and finding.status == "blocked" for finding in promotion.findings))
            self.assertEqual(cleanup.runs[0].status, "blocked")
            self.assertIn("knowledge promotion", cleanup.runs[0].reason)

    def test_approved_human_review_row_still_waits_for_completed_followup(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_promotion_repo(Path(temp_dir))
            (root / "agents/human_review_queue.md").write_text(
                "\n".join(
                    [
                        "# Human Review Queue",
                        "",
                        "| ID | Type | Status | Decision Needed | Evidence |",
                        "| --- | --- | --- | --- | --- |",
                        "| HRQ-1 | candidate_verification | approved | Run follow-up. | agents/runs/2026-04-01_weekly/final_digest.md |",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = assess_knowledge_promotion(
                root=root,
                run_id="2026-04-01_weekly",
                current_date=date(2026, 5, 24),
            )

            self.assertEqual(result.status, "waiting_for_human_review")
            self.assertFalse(result.cleanup_ready)
            self.assertTrue(any(finding.area == "human_review" and finding.status == "waiting" for finding in result.findings))


def seed_promotion_repo(root: Path) -> Path:
    run_id = "2026-04-01_weekly"
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    for path in [
        "stock_tracking/current_holdings",
        "stock_tracking/monitoring",
        "stock_tracking/rejected",
        "stock_tracking/stock_info_files/current_holdings",
        "stock_tracking/stock_info_files/monitoring",
        "stock_tracking/stock_info_files/rejected",
        "agents/runs/2026-04-01_weekly/reports/human_synthesis",
        "agents/runs/2026-04-01_weekly/reports/opportunity_assessment",
        "agents/memory",
        "docs/plans",
        "strategy",
        "archive",
    ]:
        (root / path).mkdir(parents=True, exist_ok=True)

    write_stock_csv(root / "stock_tracking/current_holdings/current_holdings.csv", [])
    write_stock_csv(
        root / "stock_tracking/monitoring/monitoring.csv",
        ["ABC,ABC Corp,NASDAQ,US,Technology,Software,monitoring,stock_tracking/stock_info_files/monitoring/ABC.md"],
    )
    write_stock_csv(root / "stock_tracking/rejected/rejected.csv", [])
    (root / "stock_tracking/stock_info_files/monitoring/ABC.md").write_text(
        f"# ABC\n\n## Automated Factual Updates\n\n| Date | Update ID | Area | Summary | Source |\n| --- | --- | --- | --- | --- |\n| 2026-05-24 | AUTOFACT-{run_id}-ABC | assessment_summary | Run facts promoted. | [report](agents/runs/{run_id}/reports/opportunity_assessment/ABC_opportunity_assessment.md) |\n",
        encoding="utf-8",
    )
    (root / "stock_tracking/current_holdings/current_holdings_state.md").write_text("# Holdings State\n", encoding="utf-8")
    (root / "stock_tracking/monitoring/monitoring_state.md").write_text(
        f"# Monitoring State\n\n## Automated State Updates\n\n| Date | Update ID | Category | Summary | Source |\n| --- | --- | --- | --- | --- |\n| 2026-05-24 | CATSTATE-{run_id} | monitoring | 1 monitored stock. | run |\n",
        encoding="utf-8",
    )
    (root / "stock_tracking/rejected/rejected_state.md").write_text("# Rejected State\n", encoding="utf-8")
    (root / "docs/plans/human_research_requests.md").write_text("# Human Requests\n", encoding="utf-8")
    (root / "strategy/research_priorities.md").write_text("# Priorities\n", encoding="utf-8")
    (root / "agents/human_review_queue.md").write_text(
        "# Human Review Queue\n\n| ID | Type | Status | Decision Needed | Evidence |\n| --- | --- | --- | --- | --- |\n",
        encoding="utf-8",
    )
    (root / "archive/research_index.md").write_text(f"# Index\n\nagents/runs/{run_id}/run_summary.md\n", encoding="utf-8")

    run_dir = root / "agents" / "runs" / run_id
    for name in ("run_summary", "quality_report", "memory_reflection", "finalization", "final_digest"):
        (run_dir / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")
        (run_dir / f"{name}.json").write_text('{"ok": true}\n', encoding="utf-8")
    (run_dir / "memory_update_drafts.json").write_text('{"items": []}\n', encoding="utf-8")
    (run_dir / "memory_update_drafts.md").write_text("# Memory Update Drafts\n\n- No memory update proposals.\n", encoding="utf-8")
    (run_dir / "reports/human_synthesis/ABC_synthesis_pack.md").write_text("# ABC Pack\n", encoding="utf-8")
    (run_dir / "reports/human_synthesis/ABC_final_human_report.md").write_text("# ABC Final\n", encoding="utf-8")
    (run_dir / "reports/opportunity_assessment/ABC_opportunity_assessment.md").write_text("# ABC Assessment\n", encoding="utf-8")
    return root


def write_stock_csv(path: Path, rows: list[str]) -> None:
    header = "ticker,company_name,exchange,country,sector,industry,status,stock_info_file"
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
