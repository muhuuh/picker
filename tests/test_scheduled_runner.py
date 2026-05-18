from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.agent_runtime.fanout import AgentFanoutItemResult, AgentFanoutResult
from stock_research.agent_runtime.outputs import OrchestratorDecision
from stock_research.agent_runtime.runner import AgentRuntimeResult
from stock_research.scheduled_runner import determine_status, run_weekly_research_workflow
from stock_research.weekly_digest import WeeklyDigest


class ScheduledRunnerTests(unittest.TestCase):
    def test_weekly_workflow_dry_run_reaches_framework_boundary_without_writing(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))

            result, paths = run_weekly_research_workflow(root=root, current_date=date(2026, 5, 5))

            self.assertEqual(result.status, "dry_run")
            self.assertEqual(paths, [])
            self.assertEqual(result.steps["framework_boundary"]["status"], "resolved")
            self.assertEqual(result.steps["agent_orchestrator"]["status"], "not_run")
            self.assertFalse((root / "agents/runs/2026-05-09_weekly/manifest.json").exists())

    def test_weekly_workflow_write_persists_final_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))

            result, paths = run_weekly_research_workflow(root=root, current_date=date(2026, 5, 5), write=True)

            self.assertEqual(result.status, "complete")
            self.assertTrue(paths)
            self.assertTrue((root / "agents/runs/2026-05-09_weekly/manifest.json").exists())
            self.assertTrue((root / "agents/runs/2026-05-09_weekly/run_summary.md").exists())
            self.assertTrue((root / "agents/runs/2026-05-09_weekly/quality_report.md").exists())
            self.assertTrue((root / "agents/runs/2026-05-09_weekly/finalization.md").exists())
            self.assertTrue((root / "agents/runs/2026-05-09_weekly/memory_writer_review.md").exists())
            self.assertTrue((root / "agents/runs/2026-05-09_weekly/codex_supervised_review_pack.md").exists())
            self.assertTrue((root / "agents/runs/2026-05-09_weekly/orchestration_report.md").exists())
            self.assertTrue((root / "agents/human_review_digest.md").exists())
            pack_text = (root / "agents/runs/2026-05-09_weekly/codex_supervised_review_pack.md").read_text(encoding="utf-8")
            self.assertIn("Codex-Supervised Review Pack", pack_text)
            self.assertIn("Do not use API mode in the scheduled Codex-supervised automation", pack_text)
            self.assertIn("--require-final-reports", pack_text)
            self.assertEqual(result.steps["codex_review_pack"]["expected_output_path"], "agents/runs/2026-05-09_weekly/codex_supervised_review.md")
            self.assertEqual(
                result.steps["codex_review_pack"]["post_codex_quality_command"],
                "python -m stock_research quality-report --run-id 2026-05-09_weekly --write --require-final-reports",
            )
            self.assertIn("agents/runs/2026-05-09_weekly/codex_supervised_review_pack.md", result.steps["codex_review_pack"]["written_paths"])
            self.assertEqual(result.steps["human_review_digest"]["status"], "clear")

    def test_weekly_workflow_can_execute_orchestrator_with_injected_executor(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))

            result, paths = run_weekly_research_workflow(
                root=root,
                current_date=date(2026, 5, 5),
                write=True,
                execute_orchestrator=True,
                orchestrator_executor=fake_orchestrator_executor,
            )

            self.assertEqual(result.status, "needs_review")
            self.assertEqual(result.steps["agent_orchestrator"]["status"], "needs_review")
            self.assertIn("agents/runs/2026-05-09_weekly/agent_runtime_main_orchestrator.md", result.artifacts)
            self.assertTrue(root / "agents/runs/2026-05-09_weekly/orchestration_report.md" in paths)

    def test_weekly_workflow_fresh_orchestrator_can_complete_with_injected_executors(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))

            result, _paths = run_weekly_research_workflow(
                root=root,
                current_date=date(2026, 5, 5),
                write=True,
                execute_providers=True,
                execute_analysis=True,
                execute_orchestrator=True,
                provider_executor=fake_provider_executor,
                analysis_executor=fake_analysis_executor,
                orchestrator_executor=fake_ready_no_action_orchestrator_executor,
            )

            self.assertEqual(result.status, "complete")
            self.assertEqual(result.steps["agent_orchestrator"]["status"], "complete")
            self.assertEqual(result.steps["agent_orchestrator"]["quality_findings"], [])

    def test_weekly_workflow_flags_ready_orchestrator_output_from_dry_run_inputs(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(
                Path(temp_dir),
                monitoring_rows=[
                    "AAPL,Apple Inc.,NASDAQ,US,Technology,Consumer Electronics,monitoring,test,100,USD,1000,20,2026-05-01,2026-05-01,2026-05-09,stock_tracking/stock_info_files/monitoring/AAPL_apple_inc.md,test"
                ],
            )

            result, _paths = run_weekly_research_workflow(
                root=root,
                current_date=date(2026, 5, 5),
                write=True,
                execute_orchestrator=True,
                orchestrator_executor=fake_ready_orchestrator_executor,
            )

            self.assertEqual(result.status, "needs_review")
            self.assertEqual(result.steps["agent_orchestrator"]["status"], "needs_review")
            self.assertIn("were dry-run", result.steps["agent_orchestrator"]["quality_findings"][0])

    def test_weekly_workflow_can_execute_with_injected_task_executors(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir), monitoring_rows=["AAPL,Apple Inc.,NASDAQ,US,Technology,Consumer Electronics,monitoring,test,100,USD,1000,20,2026-05-01,2026-05-01,2026-05-09,stock_tracking/stock_info_files/monitoring/AAPL_apple_inc.md,test"])

            result, _paths = run_weekly_research_workflow(
                root=root,
                current_date=date(2026, 5, 5),
                execute_providers=True,
                execute_analysis=True,
                provider_executor=fake_provider_executor,
                analysis_executor=fake_analysis_executor,
            )

            self.assertEqual(result.status, "dry_run")
            self.assertGreater(len(result.steps["provider_tasks"]["executed"]), 0)
            self.assertGreater(len(result.steps["analysis_tasks"]["executed"]), 0)

    def test_weekly_workflow_execute_cleans_previous_generated_run_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(
                Path(temp_dir),
                monitoring_rows=[
                    "AAPL,Apple Inc.,NASDAQ,US,Technology,Consumer Electronics,monitoring,test,100,USD,1000,20,2026-05-01,2026-05-01,2026-05-09,stock_tracking/stock_info_files/monitoring/AAPL_apple_inc.md,test"
                ],
            )
            stale_packet = root / "agents/runs/2026-05-09_weekly/evidence_packets/stale.json"
            stale_packet.parent.mkdir(parents=True)
            stale_packet.write_text("{}", encoding="utf-8")
            stale_report = root / "agents/runs/2026-05-09_weekly/reports/stale.md"
            stale_report.parent.mkdir(parents=True)
            stale_report.write_text("# stale\n", encoding="utf-8")
            stale_portfolio = root / "agents/runs/2026-05-09_weekly/portfolio_review/stale.md"
            stale_portfolio.parent.mkdir(parents=True)
            stale_portfolio.write_text("# stale portfolio\n", encoding="utf-8")
            stale_memory = root / "agents/runs/2026-05-09_weekly/memory_evaluation/stale.md"
            stale_memory.parent.mkdir(parents=True)
            stale_memory.write_text("# stale memory\n", encoding="utf-8")

            run_weekly_research_workflow(
                root=root,
                current_date=date(2026, 5, 5),
                write=True,
                execute_providers=True,
                provider_executor=fake_provider_executor,
            )

            self.assertFalse(stale_packet.exists())
            self.assertFalse(stale_report.exists())
            self.assertFalse(stale_portfolio.exists())
            self.assertFalse(stale_memory.exists())

    def test_weekly_workflow_can_write_company_research_for_tracked_tickers(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(
                Path(temp_dir),
                monitoring_rows=[
                    "AAPL,Apple Inc.,NASDAQ,US,Technology,Consumer Electronics,monitoring,test,100,USD,1000,20,2026-05-01,2026-05-01,2026-05-09,stock_tracking/stock_info_files/monitoring/AAPL_apple_inc.md,test"
                ],
            )

            result, paths = run_weekly_research_workflow(
                root=root,
                current_date=date(2026, 5, 5),
                write=True,
                execute_company_research=True,
                company_research_executor=fake_company_research_executor,
            )

            report_path = root / "agents/runs/2026-05-09_weekly/company_research/AAPL_company_research.md"
            self.assertEqual(result.steps["company_research"]["status"], "complete")
            self.assertEqual(result.steps["company_research"]["tickers"], ["AAPL"])
            self.assertTrue(report_path.exists())
            self.assertTrue(report_path in paths)

    def test_open_human_review_digest_does_not_make_run_fail(self):
        digest = WeeklyDigest(
            run_id="2026-05-09_weekly",
            status="needs_review",
            ticker_count=1,
            open_review_count=20,
            tickers=[],
            next_actions=["Review human-review digest."],
            quality_findings=[],
        )

        status = determine_status(
            write=True,
            provider_result={"errors": []},
            analysis_result={"errors": [], "skipped": []},
            quality_report=None,
            finalization=None,
            weekly_digest=digest,
        )

        self.assertEqual(status, "complete")


def seed_repo(root: Path, monitoring_rows: list[str] | None = None) -> Path:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking/current_holdings").mkdir(parents=True)
    (root / "stock_tracking/monitoring").mkdir(parents=True)
    (root / "stock_tracking/rejected").mkdir(parents=True)
    (root / "stock_tracking/stock_info_files/monitoring").mkdir(parents=True)
    (root / "agents/memory").mkdir(parents=True)
    (root / "docs/plans").mkdir(parents=True)
    (root / "strategy").mkdir(parents=True)
    write_stock_csv(root / "stock_tracking/current_holdings/current_holdings.csv", [])
    write_stock_csv(root / "stock_tracking/monitoring/monitoring.csv", monitoring_rows or [])
    write_stock_csv(root / "stock_tracking/rejected/rejected.csv", [])
    for category in ("current_holdings", "monitoring", "rejected"):
        title = category.replace("_", " ").title()
        (root / f"stock_tracking/{category}/{category}_state.md").write_text(
            f"# {title} State\n\nLast updated: 2026-05-01\n\n## Current View\n\n- Test seed.\n",
            encoding="utf-8",
        )
    (root / "docs/plans/human_research_requests.md").write_text("# Human Research Requests\n", encoding="utf-8")
    (root / "strategy/research_priorities.md").write_text("# Research Priorities\n", encoding="utf-8")
    (root / "agents/human_review_queue.md").write_text("# Human Review Queue\n", encoding="utf-8")
    return root


def write_stock_csv(path: Path, rows: list[str]) -> None:
    header = "ticker,company_name,exchange,country,sector,industry,status,source,price,currency,market_cap,pe_ratio,date_found,date_last_updated,next_review_date,stock_info_file,notes"
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")


def fake_provider_executor(root: Path, task: dict, current_date: date | None):
    return {"packet_id": f"packet_{task['id']}", "paths": [str(root / "fake_provider.json")]}


def fake_analysis_executor(root: Path, task: dict, current_date: date | None):
    return {"packet_id": f"packet_{task['id']}", "paths": [str(root / "fake_analysis.json")]}


def fake_orchestrator_executor(context, prompt: str, model: str | None):
    report_path = context.run_dir / "agent_runtime_main_orchestrator.md"
    json_path = context.run_dir / "agent_runtime_main_orchestrator.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("# Agent Runtime Report\n", encoding="utf-8")
    json_path.write_text(
        '{"agent_id":"main_orchestrator","run_id":"2026-05-09_weekly","status":"partial","summary":"Fake SDK orchestrator result for scheduled runner tests.","memory_item_ids_used":[]}\n',
        encoding="utf-8",
    )
    return AgentRuntimeResult(
        agent_id="main_orchestrator",
        final_output={
            "agent_id": "main_orchestrator",
            "run_id": context.run_id,
            "status": "partial",
            "summary": "Fake SDK orchestrator result for scheduled runner tests.",
            "memory_item_ids_used": [],
        },
        trace_id=context.trace_id,
        group_id=context.trace_group_id,
        quality_findings=[],
        written_paths=(str(report_path),),
    )


def fake_ready_orchestrator_executor(context, prompt: str, model: str | None):
    report_path = context.run_dir / "agent_runtime_main_orchestrator.md"
    json_path = context.run_dir / "agent_runtime_main_orchestrator.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("# Agent Runtime Report\n", encoding="utf-8")
    final_output = {
            "agent_id": "main_orchestrator",
            "run_id": context.run_id,
            "status": "ready",
            "summary": "Fake SDK orchestrator result with enough detail to represent a ready scheduled synthesis after deterministic work.",
            "memory_item_ids_used": [],
            "file_update_proposals": [
                {
                    "target_file": "stock_tracking/stock_info_files/monitoring/AAPL_apple_inc.md",
                    "update_type": "company_file_update",
                    "summary": "Fake update proposal.",
                    "confidence": "medium",
                    "source_ids": ["fake_source"],
                    "needs_human_review": False,
                }
            ],
            "sources": [
                {
                    "source_id": "fake_source",
                    "title": "Fake source",
                    "url": "https://example.com",
                    "artifact_path": "",
                    "confidence": "medium",
                }
            ],
        }
    json_path.write_text(json.dumps(final_output), encoding="utf-8")
    (context.run_dir / "run_metrics.md").write_text(
        "# Run Metrics\n\n"
        "| metric | status | started_at | ended_at | detail |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| agent_run:main_orchestrator | complete | 2026-05-05T00:00:00+00:00 | 2026-05-05T00:00:01+00:00 | fake ready result |\n",
        encoding="utf-8",
    )
    return AgentRuntimeResult(
        agent_id="main_orchestrator",
        final_output=final_output,
        trace_id=context.trace_id,
        group_id=context.trace_group_id,
        quality_findings=[],
        written_paths=(str(report_path),),
    )


def fake_ready_no_action_orchestrator_executor(context, prompt: str, model: str | None):
    report_path = context.run_dir / "agent_runtime_main_orchestrator.md"
    json_path = context.run_dir / "agent_runtime_main_orchestrator.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("# Agent Runtime Report\n", encoding="utf-8")
    final_output = {
            "agent_id": "main_orchestrator",
            "run_id": context.run_id,
            "status": "ready",
            "summary": "Fake SDK orchestrator result with enough detail to represent a ready scheduled synthesis with no actionable output.",
            "memory_item_ids_used": [],
            "file_update_proposals": [],
            "alerts": [],
            "sources": [],
        }
    json_path.write_text(json.dumps(final_output), encoding="utf-8")
    (context.run_dir / "run_metrics.md").write_text(
        "# Run Metrics\n\n"
        "| metric | status | started_at | ended_at | detail |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| agent_run:main_orchestrator | complete | 2026-05-05T00:00:00+00:00 | 2026-05-05T00:00:01+00:00 | fake ready result |\n",
        encoding="utf-8",
    )
    return AgentRuntimeResult(
        agent_id="main_orchestrator",
        final_output=final_output,
        trace_id=context.trace_id,
        group_id=context.trace_group_id,
        quality_findings=[],
        written_paths=(str(report_path),),
    )


def fake_company_research_executor(context, ticker: str, model: str | None):
    decision = OrchestratorDecision(
        agent_id="company_research_orchestrator",
        run_id=context.run_id,
        status="ready",
        summary=f"Fake company research decision for {ticker} with enough detail for scheduled-run artifact tests.",
        memory_item_ids_used=list(context.memory_item_ids[:1]),
    )
    fanout = AgentFanoutResult(
        status="complete",
        results=(
            AgentFanoutItemResult(
                task_id=f"financial_{ticker.lower()}",
                agent_id="financial_specialist",
                task="financial specialist",
                status="complete",
                final_output={
                    "agent_id": "financial_specialist",
                    "subject_type": "company",
                    "subject_id": ticker,
                    "status": "ready",
                    "summary": "Fake financial specialist result for scheduled company research tests.",
                    "memory_item_ids_used": list(context.memory_item_ids[:1]),
                },
            ),
        ),
        metrics=(),
    )
    return decision, fanout


if __name__ == "__main__":
    unittest.main()
