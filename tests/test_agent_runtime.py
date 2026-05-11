from pathlib import Path
import asyncio
from contextlib import redirect_stdout
from datetime import date
from dataclasses import replace
import io
import json
from types import SimpleNamespace
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from agents import Agent

from stock_research.agent_runtime.context import build_research_run_context
from stock_research.agent_runtime.fanout import AgentFanoutTask, fanout_result_to_dict, run_agent_fanout_sync
from stock_research.agent_runtime.orchestrators.company_research import (
    build_company_research_input,
    build_company_research_fanout_tasks,
    build_company_research_packet,
    run_company_research_sub_orchestrator_sync,
)
from stock_research.agent_runtime.orchestrators.market_research import (
    build_market_research_fanout_tasks,
    build_market_research_input,
    build_market_research_packet,
    run_market_research_sub_orchestrator_sync,
)
from stock_research.agent_runtime.orchestrators.memory_evaluation import (
    aggregate_memory_evaluation,
    build_memory_evaluation_input,
    build_memory_evaluation_packet,
    write_memory_evaluation_report,
)
from stock_research.agent_runtime.orchestrators.portfolio_review import (
    aggregate_portfolio_review,
    build_portfolio_review_input,
    build_portfolio_review_packet,
    write_portfolio_review_report,
)
from stock_research.agent_runtime.outputs import OrchestratorDecision
from stock_research.agent_runtime.reports import (
    build_main_orchestrator_input_packet,
    build_orchestrator_input,
    evaluate_runtime_output_quality,
    output_to_dict,
)
from stock_research.agent_runtime.registry import build_agent, build_agent_tool, list_agent_specs
from stock_research.agent_runtime.runner import AgentRuntimeResult, build_run_config, reported_memory_item_ids, run_agent_sync
from stock_research.agent_runtime.tracing import LocalRunHooks, LocalRunMetric, LocalRunTelemetry, write_run_metrics
from stock_research.agent_runtime.tools.analysis_tools import run_analysis_tasks_for_context
from stock_research.agent_runtime.tools.provider_tools import run_provider_tasks_for_context
from stock_research.agent_runtime.tools.repo_tools import list_evidence_packets_data, load_evidence_packet_data, load_memory_prompt_context_for_task
from stock_research.cli import main
from stock_research.evidence import Source, new_packet, write_packet


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_runtime_test_repo(root: Path) -> Path:
    (root / "AGENTS.md").write_text("# Test agents\n", encoding="utf-8")
    (root / "stock_tracking").mkdir()
    memory_dir = root / "agents" / "memory"
    memory_dir.mkdir(parents=True)
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

    run_dir = root / "agents" / "runs" / "test_weekly"
    run_dir.mkdir(parents=True)
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "manifest_id": "weekly_test",
                "provider_tasks": [
                    {
                        "id": "exa_news_aapl",
                        "provider": "exa",
                        "tool": "search",
                        "subject_type": "company",
                        "subject_id": "AAPL",
                        "priority": "high",
                        "args": {"query": "AAPL news", "run_id": "test_weekly"},
                        "reason": "test provider task",
                    }
                ],
                "analysis_tasks": [
                    {
                        "id": "financial_compare_aapl",
                        "tool": "financial_compare",
                        "subject_type": "company",
                        "subject_id": "AAPL",
                        "priority": "high",
                        "args": {"ticker": "AAPL", "run_id": "test_weekly"},
                        "depends_on": [],
                        "reason": "test analysis dependency",
                    },
                    {
                        "id": "financial_review_aapl",
                        "tool": "financial_review",
                        "subject_type": "company",
                        "subject_id": "AAPL",
                        "priority": "high",
                        "args": {"ticker": "AAPL", "run_id": "test_weekly"},
                        "depends_on": ["financial_compare_aapl"],
                        "reason": "test analysis task",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return manifest_path


def write_company_research_test_artifacts(root: Path) -> None:
    monitoring_dir = root / "stock_tracking" / "monitoring"
    company_dir = root / "stock_tracking" / "stock_info_files" / "monitoring"
    monitoring_dir.mkdir(parents=True, exist_ok=True)
    company_dir.mkdir(parents=True, exist_ok=True)
    (monitoring_dir / "monitoring.csv").write_text(
        "ticker,name,stock_info_file\nAAPL,Apple Inc.,stock_tracking/stock_info_files/monitoring/AAPL.md\n",
        encoding="utf-8",
    )
    (company_dir / "AAPL.md").write_text("# AAPL\n", encoding="utf-8")
    run_dir = root / "agents" / "runs" / "test_weekly"
    reports_dir = run_dir / "reports"
    (reports_dir / "financial_data_specialist").mkdir(parents=True, exist_ok=True)
    (reports_dir / "company_news_specialist").mkdir(parents=True, exist_ok=True)
    (reports_dir / "financial_data_specialist" / "AAPL_financial_review.md").write_text("# Financial Review\n", encoding="utf-8")
    (reports_dir / "company_news_specialist" / "AAPL_company_news_review.md").write_text("# Company News Review\n", encoding="utf-8")
    evidence_dir = run_dir / "evidence_packets"
    source = Source(
        source_id="src",
        provider="test",
        source_type="internal",
        artifact_path="agents/runs/test_weekly/raw/test.json",
    )
    for provider in ("financial_data_specialist", "company_news_specialist", "sec_edgar", "xai_grok"):
        packet = new_packet(
            provider=provider,
            subject_type="company",
            subject_id="AAPL",
            time_window="test",
            current_date=date(2026, 5, 10),
            sources=[source],
        )
        write_packet(packet, evidence_dir / f"{packet.packet_id}.json")


def write_market_research_test_artifacts(root: Path) -> Path:
    run_dir = root / "agents" / "runs" / "test_weekly"
    manifest_path = run_dir / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "manifest_id": "weekly_test",
                "inputs": {
                    "research_priorities": [
                        {
                            "Topic": "European grid infrastructure",
                            "Type": "industry",
                            "Priority": "high",
                            "Status": "active",
                        }
                    ]
                },
                "provider_tasks": [
                    {
                        "id": "exa_research_priority_european_grid_infrastructure",
                        "provider": "exa",
                        "tool": "search",
                        "subject_type": "industry",
                        "subject_id": "european_grid_infrastructure",
                        "priority": "high",
                        "source_bucket": "research_priorities",
                        "args": {"mode": "industry", "query": "European grid infrastructure", "run_id": "test_weekly"},
                    },
                    {
                        "id": "exa_discovery_priority_european_grid_infrastructure",
                        "provider": "exa",
                        "tool": "search",
                        "subject_type": "industry",
                        "subject_id": "european_grid_infrastructure",
                        "priority": "high",
                        "source_bucket": "research_priorities",
                        "args": {"mode": "company", "query": "European grid infrastructure public companies", "run_id": "test_weekly"},
                    },
                    {
                        "id": "xai_x_search_priority_european_grid_infrastructure",
                        "provider": "xai_grok",
                        "tool": "x_search",
                        "subject_type": "industry",
                        "subject_id": "european_grid_infrastructure",
                        "priority": "high",
                        "source_bucket": "research_priorities",
                        "args": {
                            "prompt": "Search X for European grid infrastructure niche companies rumors hype",
                            "run_id": "test_weekly",
                            "from_date": "2026-04-18",
                            "to_date": "2026-05-09",
                            "enable_image_understanding": True,
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    evidence_dir = run_dir / "evidence_packets"
    source = Source(
        source_id="src",
        provider="test",
        source_type="internal",
        artifact_path="agents/runs/test_weekly/raw/test.json",
    )
    for provider, suffix in (("exa", "industry"), ("exa", "company_discovery"), ("xai_grok", "x_search")):
        packet = new_packet(
            provider=provider,
            subject_type="industry",
            subject_id="european_grid_infrastructure",
            time_window="test",
            current_date=date(2026, 5, 10),
            sources=[source],
        )
        packet = replace(packet, packet_id=f"{packet.packet_id}_{suffix}")
        write_packet(packet, evidence_dir / f"{packet.packet_id}_{provider}.json")
    return manifest_path


def write_portfolio_review_test_artifacts(root: Path) -> None:
    holdings_dir = root / "stock_tracking" / "current_holdings"
    monitoring_dir = root / "stock_tracking" / "monitoring"
    rejected_dir = root / "stock_tracking" / "rejected"
    company_dir = root / "stock_tracking" / "stock_info_files" / "monitoring"
    holdings_dir.mkdir(parents=True, exist_ok=True)
    monitoring_dir.mkdir(parents=True, exist_ok=True)
    rejected_dir.mkdir(parents=True, exist_ok=True)
    company_dir.mkdir(parents=True, exist_ok=True)
    (holdings_dir / "current_holdings.csv").write_text(
        "ticker,company_name,stock_info_file,date_last_updated\n",
        encoding="utf-8",
    )
    (monitoring_dir / "monitoring.csv").write_text(
        "ticker,company_name,stock_info_file,date_last_updated\nAAPL,Apple Inc.,stock_tracking/stock_info_files/monitoring/AAPL.md,\nMSFT,Microsoft,stock_tracking/stock_info_files/monitoring/MSFT.md,2026-05-10\n",
        encoding="utf-8",
    )
    (company_dir / "MSFT.md").write_text("# MSFT\n", encoding="utf-8")
    (rejected_dir / "rejected.csv").write_text(
        "ticker,company_name,next_eligible_review_date,date_last_updated\nOLD,Old Co,2026-06-01,2026-05-10\n",
        encoding="utf-8",
    )
    (root / "agents").mkdir(parents=True, exist_ok=True)
    (root / "agents" / "human_review_queue.md").write_text(
        "\n".join(
            [
                "# Human Review Queue",
                "",
                "| ID | Date Added | Item | Decision Needed | Priority | Status | Related Files | Evidence / Run Link | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| HRQ-1000 | 2026-05-11 | Review AAPL company file update. | Approve/reject/more research. | medium | open | stock_tracking/stock_info_files/monitoring/AAPL.md | agents/runs/test_weekly/orchestrator_update_proposals.md#ORP-1 |  |",
                "| HRQ-1001 | 2026-05-11 | Approved candidate verification. | Run follow-up. | medium | approved | agents/runs/test_weekly/market_research | agents/runs/test_weekly/market_research/candidate_review.md#CRG-1 |  |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    market_dir = root / "agents" / "runs" / "test_weekly" / "market_research"
    market_dir.mkdir(parents=True, exist_ok=True)
    (market_dir / "candidate_verification_result.md").write_text("# Candidate Verification Result\n", encoding="utf-8")


def write_memory_evaluation_test_artifacts(root: Path) -> None:
    run_dir = root / "agents" / "runs" / "test_weekly"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_summary.md").write_text("# Run Summary\n", encoding="utf-8")
    (run_dir / "quality_report.md").write_text("# Quality Report\n", encoding="utf-8")
    (run_dir / "run_metrics.md").write_text(
        "\n".join(
            [
                "# Run Metrics",
                "",
                "| metric | status | started_at | ended_at | memory_item_ids | detail |",
                "| --- | --- | --- | --- | --- | --- |",
                "| memory_context:main_orchestrator | injected | 2026-05-10T00:00:00+00:00 | 2026-05-10T00:00:00+00:00 | orch-test | memory injected |",
                "| memory_output:main_orchestrator | reported | 2026-05-10T00:00:00+00:00 | 2026-05-10T00:00:00+00:00 | orch-test | memory reported |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "memory_reflection.json").write_text(
        json.dumps(
            {
                "run_id": "test_weekly",
                "issues": [],
                "memory_update_proposals": [],
                "metrics": {"sdk_metric_rows": 2},
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "memory_reflection.md").write_text("# Memory Reflection\n", encoding="utf-8")
    (run_dir / "memory_update_drafts.json").write_text(
        json.dumps(
            {
                "run_id": "test_weekly",
                "items": [
                    {
                        "proposal_id": "proposal-1",
                        "status": "ready",
                        "target_file": "evaluation_metrics.md",
                        "reason": "test",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "memory_update_drafts.md").write_text("# Memory Drafts\n", encoding="utf-8")
    (run_dir / "finalization.json").write_text(json.dumps({"status": "needs_review"}), encoding="utf-8")
    (run_dir / "finalization.md").write_text("# Finalization\n", encoding="utf-8")
    memory_dir = root / "agents" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / "recurring_failures.json").write_text(json.dumps({"patterns": [], "memory_update_proposals": []}), encoding="utf-8")
    (memory_dir / "recurring_failures.md").write_text("# Recurring Failures\n", encoding="utf-8")


class AgentRuntimeTests(unittest.TestCase):
    def test_registry_lists_orchestrator_and_specialist(self):
        specs = {spec.agent_id: spec for spec in list_agent_specs()}

        self.assertEqual(specs["main_orchestrator"].role, "orchestrator")
        self.assertEqual(specs["company_research_orchestrator"].role, "orchestrator")
        self.assertEqual(specs["market_research_orchestrator"].role, "orchestrator")
        self.assertEqual(specs["memory_evaluation_orchestrator"].role, "orchestrator")
        self.assertEqual(specs["portfolio_review_orchestrator"].role, "orchestrator")
        self.assertEqual(specs["company_news_specialist"].role, "specialist")
        self.assertEqual(specs["company_search_specialist"].role, "specialist")
        self.assertEqual(specs["discovery_specialist"].role, "specialist")
        self.assertEqual(specs["exa_industry_specialist"].role, "specialist")
        self.assertEqual(specs["filing_specialist"].role, "specialist")
        self.assertEqual(specs["financial_specialist"].role, "specialist")
        self.assertEqual(specs["grok_discovery_specialist"].role, "specialist")
        self.assertEqual(specs["quality_reviewer_specialist"].role, "specialist")
        self.assertEqual(specs["risk_thesis_specialist"].role, "specialist")
        self.assertEqual(specs["sentiment_specialist"].role, "specialist")
        self.assertEqual(specs["writer_specialist"].role, "specialist")

    def test_build_research_context_includes_trace_and_memory(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="openai agents sdk runtime")

        self.assertEqual(context.root, REPO_ROOT)
        self.assertEqual(context.run_dir, REPO_ROOT / "agents" / "runs" / "test_weekly")
        self.assertTrue(context.trace_id.startswith("trace_"))
        self.assertIn("Operational Memory Context", context.memory_context)
        self.assertTrue(context.memory_item_ids)
        self.assertGreaterEqual(len(context.known_memory_item_ids), len(context.memory_item_ids))

    def test_main_orchestrator_exposes_company_news_specialist_as_tool(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="main orchestrator")
        agent = build_agent("main_orchestrator", context)
        tool_names = {getattr(tool, "name", type(tool).__name__) for tool in agent.tools}

        self.assertIsInstance(agent, Agent)
        self.assertIn("load_run_markdown", tool_names)
        self.assertIn("load_operational_memory", tool_names)
        self.assertIn("load_memory_prompt_context", tool_names)
        self.assertIn("load_repo_map", tool_names)
        self.assertIn("load_run_summary", tool_names)
        self.assertIn("load_quality_report", tool_names)
        self.assertIn("list_evidence_packets", tool_names)
        self.assertIn("load_evidence_packet", tool_names)
        self.assertIn("load_stock_tracking_csv", tool_names)
        self.assertIn("run_provider_tasks_guarded", tool_names)
        self.assertIn("run_analysis_tasks_guarded", tool_names)
        self.assertIn("company_research_orchestrator", tool_names)
        self.assertIn("market_research_orchestrator", tool_names)
        self.assertIn("portfolio_review_orchestrator", tool_names)
        self.assertIn("memory_evaluation_orchestrator", tool_names)
        self.assertIn("company_news_specialist", tool_names)
        self.assertIn("company_search_specialist", tool_names)
        self.assertIn("discovery_specialist", tool_names)
        self.assertIn("exa_industry_specialist", tool_names)
        self.assertIn("filing_specialist", tool_names)
        self.assertIn("financial_specialist", tool_names)
        self.assertIn("grok_discovery_specialist", tool_names)
        self.assertIn("quality_reviewer_specialist", tool_names)
        self.assertIn("risk_thesis_specialist", tool_names)
        self.assertIn("sentiment_specialist", tool_names)
        self.assertIn("writer_specialist", tool_names)
        self.assertNotIn("memory_apply_updates", tool_names)
        self.assertNotIn("apply_memory_updates", tool_names)
        self.assertNotIn("memory_writer_apply", tool_names)
        self.assertNotIn("write_company_file", tool_names)

    def test_provider_tool_plans_by_default_without_execute_permission(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = write_runtime_test_repo(root)
            context = build_research_run_context(
                root=root,
                run_id="test_weekly",
                task="provider tool",
                manifest_path=manifest_path,
            )

            result = run_provider_tasks_for_context(context, provider="exa")

        self.assertEqual(result["status"], "planned")
        self.assertEqual(result["mode"], "dry_run")
        self.assertEqual(result["planned_count"], 1)
        self.assertEqual(result["planned"][0]["id"], "exa_news_aapl")

    def test_provider_tool_blocks_execute_without_permission(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = write_runtime_test_repo(root)
            context = build_research_run_context(
                root=root,
                run_id="test_weekly",
                task="provider tool",
                manifest_path=manifest_path,
            )

            result = run_provider_tasks_for_context(context, provider="exa", execute=True)

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason"], "provider_execution_not_permitted")

    def test_provider_tool_execute_allowed_uses_injected_executor(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = write_runtime_test_repo(root)
            context = build_research_run_context(
                root=root,
                run_id="test_weekly",
                task="provider tool",
                manifest_path=manifest_path,
                dry_run=False,
                execute_providers=True,
            )

            result = run_provider_tasks_for_context(
                context,
                task_id="exa_news_aapl",
                execute=True,
                executor=lambda _root, task, _today: {"packet_id": f"packet-{task['id']}", "paths": []},
            )

        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["mode"], "execute")
        self.assertEqual(result["executed"][0]["packet_id"], "packet-exa_news_aapl")

    def test_analysis_tool_blocks_execute_without_permission(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = write_runtime_test_repo(root)
            context = build_research_run_context(
                root=root,
                run_id="test_weekly",
                task="analysis tool",
                manifest_path=manifest_path,
            )

            result = run_analysis_tasks_for_context(context, tool="financial_compare", execute=True)

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason"], "analysis_execution_not_permitted")

    def test_analysis_tool_execute_allowed_respects_dependencies(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = write_runtime_test_repo(root)
            context = build_research_run_context(
                root=root,
                run_id="test_weekly",
                task="analysis tool",
                manifest_path=manifest_path,
                dry_run=False,
                execute_analysis=True,
            )

            result = run_analysis_tasks_for_context(
                context,
                execute=True,
                executor=lambda _root, task, _today: {"packet_id": f"packet-{task['id']}", "paths": []},
            )

        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["mode"], "execute")
        self.assertEqual([item["id"] for item in result["executed"]], ["financial_compare_aapl", "financial_review_aapl"])

    def test_company_news_context_uses_specialist_memory(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="company news specialist")

        self.assertIn("memory-2026-05-04-company-news-specialist-review-is-implemented", context.memory_item_ids)
        self.assertIn("Company-news specialist review is implemented", context.memory_context)

    def test_financial_context_uses_specialist_memory(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="financial specialist")

        self.assertIn("memory-2026-05-04-financial-data-specialist-review-is-implemented", context.memory_item_ids)
        self.assertIn("Financial-data specialist review is implemented", context.memory_context)

    def test_company_search_context_uses_exa_memory(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="Exa company search specialist")

        self.assertIn("source-2026-05-03-exa-headers-and-modes", context.memory_item_ids)
        self.assertIn("Use Exa search modes deliberately", context.memory_context)

    def test_filing_context_uses_sec_memory(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="SEC filing specialist")

        self.assertIn("source-2026-05-03-sec-user-agent-compression", context.memory_item_ids)
        self.assertIn("SEC EDGAR is the official U.S. filings source", context.memory_context)

    def test_sentiment_context_uses_grok_memory(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="xAI Grok stock sentiment specialist")

        self.assertIn("orch-2026-05-03-direct-x-replaced", context.memory_item_ids)
        self.assertIn("source-2026-05-03-grok-social-signal", context.memory_item_ids)
        self.assertIn("Do not implement or route to direct X.com API", context.memory_context)

    def test_memory_prompt_context_tool_core_function_can_load_other_task(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="main orchestrator")

        text = load_memory_prompt_context_for_task(context, "company news specialist")

        self.assertIn("Operational Memory Context: company news specialist", text)
        self.assertIn("Company-news specialist review is implemented", text)

    def test_list_evidence_packets_data_summarizes_packets(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            evidence_dir = root / "agents" / "runs" / "test_weekly" / "evidence_packets"
            evidence_dir.mkdir(parents=True)
            (root / "AGENTS.md").write_text("# Test agents\n", encoding="utf-8")
            (root / "stock_tracking").mkdir()
            (evidence_dir / "packet.json").write_text(
                json.dumps(
                    {
                        "packet_id": "packet-1",
                        "provider": "test_provider",
                        "subject": {"type": "company", "id": "AAPL"},
                        "created_at": "2026-05-07T00:00:00",
                    }
                ),
                encoding="utf-8",
            )
            context = build_research_run_context(root=root, run_id="test_weekly", task="main orchestrator")

            data = list_evidence_packets_data(context)

        self.assertEqual(data["evidence_packets"][0]["packet_id"], "packet-1")
        self.assertEqual(data["evidence_packets"][0]["subject_id"], "AAPL")
        self.assertEqual(data["evidence_packets"][0]["subject_type"], "company")

    def test_load_evidence_packet_data_returns_packet_summary(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_runtime_test_repo(root)
            context = build_research_run_context(root=root, run_id="test_weekly", task="grok discovery specialist")
            source = Source(source_id="src", provider="exa", source_type="web", url="https://example.com")
            packet = new_packet(
                provider="exa",
                subject_type="theme",
                subject_id="grid_storage",
                time_window="test",
                current_date=date(2026, 5, 10),
                sources=[source],
            )
            write_packet(packet, context.run_dir / "evidence_packets" / f"{packet.packet_id}.json")

            data = load_evidence_packet_data(context, packet.packet_id)

        self.assertEqual(data["packet_id"], packet.packet_id)
        self.assertEqual(data["subject_id"], "grid_storage")
        self.assertEqual(data["sources"][0]["source_id"], "src")

    def test_specialist_can_be_built_as_tool(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="company news specialist")
        tool = build_agent_tool("company_news_specialist", context)

        self.assertEqual(getattr(tool, "name", ""), "company_news_specialist")

    def test_financial_specialist_can_be_built_as_tool(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="financial specialist")
        tool = build_agent_tool("financial_specialist", context)

        self.assertEqual(getattr(tool, "name", ""), "financial_specialist")

    def test_company_search_specialist_can_be_built_as_tool(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="Exa company search specialist")
        tool = build_agent_tool("company_search_specialist", context)

        self.assertEqual(getattr(tool, "name", ""), "company_search_specialist")

    def test_market_research_specialists_can_be_built_as_tools(self):
        for agent_id, task in (
            ("exa_industry_specialist", "Exa industry research specialist"),
            ("grok_discovery_specialist", "xAI Grok industry sentiment specialist"),
            ("discovery_specialist", "discovery specialist"),
        ):
            context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task=task)
            tool = build_agent_tool(agent_id, context)

            self.assertEqual(getattr(tool, "name", ""), agent_id)

    def test_filing_specialist_can_be_built_as_tool(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="SEC filing specialist")
        tool = build_agent_tool("filing_specialist", context)

        self.assertEqual(getattr(tool, "name", ""), "filing_specialist")

    def test_sentiment_specialist_can_be_built_as_tool(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="xAI Grok stock sentiment specialist")
        tool = build_agent_tool("sentiment_specialist", context)

        self.assertEqual(getattr(tool, "name", ""), "sentiment_specialist")

    def test_company_research_orchestrator_can_be_built(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="company research sub-orchestrator")
        agent = build_agent("company_research_orchestrator", context)
        tool_names = {getattr(tool, "name", type(tool).__name__) for tool in agent.tools}

        self.assertIsInstance(agent, Agent)
        self.assertIn("load_run_markdown", tool_names)
        self.assertIn("run_provider_tasks_guarded", tool_names)
        self.assertIn("run_analysis_tasks_guarded", tool_names)
        self.assertIn("company_news_specialist", tool_names)
        self.assertIn("company_search_specialist", tool_names)
        self.assertIn("filing_specialist", tool_names)
        self.assertIn("financial_specialist", tool_names)
        self.assertIn("quality_reviewer_specialist", tool_names)
        self.assertIn("risk_thesis_specialist", tool_names)
        self.assertIn("sentiment_specialist", tool_names)
        self.assertIn("writer_specialist", tool_names)
        self.assertNotIn("write_company_file", tool_names)

    def test_market_research_orchestrator_can_be_built(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="market research sub-orchestrator")
        agent = build_agent("market_research_orchestrator", context)
        tool_names = {getattr(tool, "name", type(tool).__name__) for tool in agent.tools}

        self.assertIsInstance(agent, Agent)
        self.assertIn("load_run_markdown", tool_names)
        self.assertIn("run_provider_tasks_guarded", tool_names)
        self.assertIn("exa_industry_specialist", tool_names)
        self.assertIn("grok_discovery_specialist", tool_names)
        self.assertIn("discovery_specialist", tool_names)
        self.assertIn("quality_reviewer_specialist", tool_names)
        self.assertNotIn("write_company_file", tool_names)

    def test_portfolio_review_orchestrator_can_be_built(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="portfolio review sub-orchestrator")
        agent = build_agent("portfolio_review_orchestrator", context)
        tool_names = {getattr(tool, "name", type(tool).__name__) for tool in agent.tools}

        self.assertIsInstance(agent, Agent)
        self.assertIn("load_run_markdown", tool_names)
        self.assertIn("load_stock_tracking_csv", tool_names)
        self.assertIn("quality_reviewer_specialist", tool_names)
        self.assertNotIn("write_company_file", tool_names)

    def test_memory_evaluation_orchestrator_can_be_built(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="memory evaluation sub-orchestrator")
        agent = build_agent("memory_evaluation_orchestrator", context)
        tool_names = {getattr(tool, "name", type(tool).__name__) for tool in agent.tools}

        self.assertIsInstance(agent, Agent)
        self.assertIn("load_run_markdown", tool_names)
        self.assertIn("load_operational_memory", tool_names)
        self.assertIn("quality_reviewer_specialist", tool_names)
        self.assertNotIn("memory_apply_updates", tool_names)
        self.assertNotIn("write_company_file", tool_names)

    def test_company_research_packet_groups_existing_company_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = write_runtime_test_repo(root)
            write_company_research_test_artifacts(root)
            context = build_research_run_context(
                root=root,
                run_id="test_weekly",
                task="company research sub-orchestrator",
                manifest_path=manifest_path,
            )

            packet = build_company_research_packet(context, "AAPL")
            prompt = build_company_research_input(context, "AAPL")

        lanes = {lane.lane_id: lane for lane in packet.lanes}
        self.assertEqual(packet.stock_bucket, "monitoring")
        self.assertEqual(packet.stock_info_file, "stock_tracking/stock_info_files/monitoring/AAPL.md")
        self.assertEqual(lanes["financials"].status, "ready")
        self.assertEqual(lanes["company_news"].status, "ready")
        self.assertEqual(lanes["filings"].status, "ready")
        self.assertEqual(lanes["sentiment"].status, "ready")
        self.assertEqual(lanes["company_search"].status, "missing")
        self.assertIn("Company research packet", prompt)

    def test_company_research_fanout_tasks_use_available_specialists(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = write_runtime_test_repo(root)
            write_company_research_test_artifacts(root)
            context = build_research_run_context(
                root=root,
                run_id="test_weekly",
                task="company research sub-orchestrator",
                manifest_path=manifest_path,
            )

            tasks = build_company_research_fanout_tasks(context, "AAPL", timeout_seconds=12)

        self.assertEqual(len(tasks), 8)
        self.assertEqual(
            [task.agent_id for task in tasks],
            [
                "financial_specialist",
                "company_news_specialist",
                "company_search_specialist",
                "filing_specialist",
                "sentiment_specialist",
                "risk_thesis_specialist",
                "writer_specialist",
                "quality_reviewer_specialist",
            ],
        )
        self.assertTrue(all(task.timeout_seconds == 12 for task in tasks))
        self.assertTrue(all("Company research packet" in task.prompt for task in tasks))

    def test_company_research_sub_orchestrator_aggregates_fanout_results(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = write_runtime_test_repo(root)
            write_company_research_test_artifacts(root)
            context = build_research_run_context(
                root=root,
                run_id="test_weekly",
                task="company research sub-orchestrator",
                manifest_path=manifest_path,
            )

            async def fake_runner(agent_id, _prompt, task_context, **_kwargs):
                return AgentRuntimeResult(
                    agent_id=agent_id,
                    final_output={
                        "agent_id": agent_id,
                        "subject_type": "company",
                        "subject_id": "AAPL",
                        "status": "ready",
                        "summary": "Company news evidence is adequate for this deterministic sub-orchestrator unit test.",
                        "memory_item_ids_used": list(task_context.memory_item_ids[:1]),
                    },
                    trace_id=task_context.trace_id,
                    group_id=task_context.trace_group_id,
                    quality_findings=[],
                )

            decision, fanout = run_company_research_sub_orchestrator_sync(context, "AAPL", runner=fake_runner)

        self.assertEqual(fanout.status, "complete")
        self.assertEqual(decision.agent_id, "company_research_orchestrator")
        self.assertEqual(decision.status, "partial")
        self.assertEqual(len(decision.specialist_results), 8)
        self.assertEqual(
            [result.agent_id for result in decision.specialist_results],
            [
                "financial_specialist",
                "company_news_specialist",
                "company_search_specialist",
                "filing_specialist",
                "sentiment_specialist",
                "risk_thesis_specialist",
                "writer_specialist",
                "quality_reviewer_specialist",
            ],
        )
        self.assertTrue(any("company_search" in task for task in decision.next_run_tasks))

    def test_market_research_packet_requires_grok_discovery_lane(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_runtime_test_repo(root)
            manifest_path = write_market_research_test_artifacts(root)
            context = build_research_run_context(
                root=root,
                run_id="test_weekly",
                task="market research sub-orchestrator",
                manifest_path=manifest_path,
            )

            packet = build_market_research_packet(context, "european_grid_infrastructure", "industry")
            prompt = build_market_research_input(context, "european_grid_infrastructure", "industry")
            tasks = build_market_research_fanout_tasks(context, "european_grid_infrastructure", "industry", timeout_seconds=12)

        lanes = {lane.lane_id: lane for lane in packet.lanes}
        self.assertEqual(lanes["exa_industry"].status, "ready")
        self.assertEqual(lanes["exa_company_discovery"].status, "ready")
        self.assertEqual(lanes["grok_x_discovery"].status, "ready")
        self.assertIn("Grok/X is mandatory", prompt)
        self.assertEqual(
            [task.agent_id for task in tasks],
            ["exa_industry_specialist", "grok_discovery_specialist", "discovery_specialist", "quality_reviewer_specialist"],
        )
        self.assertTrue(all(task.timeout_seconds == 12 for task in tasks))

    def test_market_research_sub_orchestrator_aggregates_fanout_results(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_runtime_test_repo(root)
            manifest_path = write_market_research_test_artifacts(root)
            context = build_research_run_context(
                root=root,
                run_id="test_weekly",
                task="market research sub-orchestrator",
                manifest_path=manifest_path,
            )

            async def fake_runner(agent_id, _prompt, task_context, **_kwargs):
                return AgentRuntimeResult(
                    agent_id=agent_id,
                    final_output={
                        "agent_id": agent_id,
                        "subject_type": "industry",
                        "subject_id": "european_grid_infrastructure",
                        "status": "ready",
                        "summary": "Market discovery evidence is adequate for this deterministic sub-orchestrator unit test.",
                        "memory_item_ids_used": list(task_context.memory_item_ids[:1]),
                    },
                    trace_id=task_context.trace_id,
                    group_id=task_context.trace_group_id,
                    quality_findings=[],
                )

            decision, fanout = run_market_research_sub_orchestrator_sync(
                context,
                "european_grid_infrastructure",
                "industry",
                runner=fake_runner,
            )

        self.assertEqual(fanout.status, "complete")
        self.assertEqual(decision.agent_id, "market_research_orchestrator")
        self.assertEqual(len(decision.specialist_results), 4)
        self.assertIn("Grok/X discovery is required", decision.summary)

    def test_portfolio_review_packet_summarizes_buckets_and_open_reviews(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_runtime_test_repo(root)
            write_portfolio_review_test_artifacts(root)
            context = build_research_run_context(root=root, run_id="test_weekly", task="portfolio review sub-orchestrator")

            packet = build_portfolio_review_packet(context)
            prompt = build_portfolio_review_input(context)
            decision = aggregate_portfolio_review(context)
            json_path, md_path = write_portfolio_review_report(context, decision)
            report = md_path.read_text(encoding="utf-8")
            json_exists = json_path.exists()

        buckets = {bucket.bucket: bucket for bucket in packet.buckets}
        self.assertEqual(buckets["monitoring"].row_count, 2)
        self.assertIn("AAPL", buckets["monitoring"].stale_tickers)
        self.assertIn("AAPL", buckets["monitoring"].missing_company_files)
        self.assertEqual(packet.open_human_review_count, 1)
        self.assertEqual(packet.approved_human_review_count, 1)
        self.assertEqual(packet.rejected_cooldown_count, 1)
        self.assertIn("Portfolio review packet", prompt)
        self.assertEqual(decision.agent_id, "portfolio_review_orchestrator")
        self.assertEqual(decision.status, "partial")
        self.assertTrue(json_exists)
        self.assertIn("Review open HRQ items", report)

    def test_memory_evaluation_packet_summarizes_learning_loop(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_runtime_test_repo(root)
            write_memory_evaluation_test_artifacts(root)
            context = build_research_run_context(root=root, run_id="test_weekly", task="memory evaluation sub-orchestrator")

            packet = build_memory_evaluation_packet(context)
            prompt = build_memory_evaluation_input(context)
            decision = aggregate_memory_evaluation(context)
            json_path, md_path = write_memory_evaluation_report(context, decision)
            report = md_path.read_text(encoding="utf-8")
            json_exists = json_path.exists()

        self.assertEqual(packet.ready_memory_update_draft_count, 1)
        self.assertEqual(packet.sdk_metric_rows, 2)
        self.assertEqual(packet.status, "needs_human_review")
        self.assertIn("Memory evaluation packet", prompt)
        self.assertEqual(decision.agent_id, "memory_evaluation_orchestrator")
        self.assertTrue(json_exists)
        self.assertIn("ready memory update drafts", report)

    def test_run_config_uses_trace_metadata_without_sensitive_data(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="main orchestrator")
        run_config = build_run_config(context, model="gpt-5.5")

        self.assertEqual(run_config.model, "gpt-5.5")
        self.assertEqual(run_config.workflow_name, "stock-research-agent-runtime")
        self.assertEqual(run_config.trace_id, context.trace_id)
        self.assertFalse(run_config.trace_include_sensitive_data)
        self.assertEqual(run_config.trace_metadata["run_id"], "test_weekly")

    def test_write_run_metrics_records_memory_ids(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_runtime_test_repo(root)
            context = build_research_run_context(root=root, run_id="test_weekly", task="sdk tool guardrails")

            path = write_run_metrics(
                context,
                [
                    LocalRunMetric(
                        name="memory_context:Main",
                        status="injected",
                        started_at="2026-05-10T00:00:00+00:00",
                        ended_at="2026-05-10T00:00:00+00:00",
                        detail="memory injected",
                        memory_item_ids=("orch-test-memory",),
                    )
                ],
            )
            text = path.read_text(encoding="utf-8")

        self.assertIn("memory_item_ids", text)
        self.assertIn("orch-test-memory", text)

    def test_run_agent_sync_writes_blocked_result_on_timeout(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_runtime_test_repo(root)
            context = build_research_run_context(root=root, run_id="test_weekly", task="main orchestrator")

            async def timeout_run_agent(*_args, **_kwargs):
                raise TimeoutError()

            with patch("stock_research.agent_runtime.runner.run_agent", timeout_run_agent):
                result = run_agent_sync("main_orchestrator", "prompt", context, write=True, timeout_seconds=0.01)

            report = json.loads((context.run_dir / "agent_runtime_main_orchestrator.json").read_text(encoding="utf-8"))
            metrics = (context.run_dir / "run_metrics.md").read_text(encoding="utf-8")

        self.assertEqual(report["status"], "blocked")
        self.assertIn("timed out", result.quality_findings[0])
        self.assertIn("| agent_run:main_orchestrator | timeout |", metrics)

    def test_run_agent_sync_writes_blocked_result_on_runtime_error(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_runtime_test_repo(root)
            context = build_research_run_context(root=root, run_id="test_weekly", task="main orchestrator")

            async def failing_run_agent(*_args, **_kwargs):
                raise RuntimeError("provider tool exploded")

            with patch("stock_research.agent_runtime.runner.run_agent", failing_run_agent):
                result = run_agent_sync("main_orchestrator", "prompt", context, write=True)

            report = json.loads((context.run_dir / "agent_runtime_main_orchestrator.json").read_text(encoding="utf-8"))
            metrics = (context.run_dir / "run_metrics.md").read_text(encoding="utf-8")

        self.assertEqual(report["status"], "blocked")
        self.assertIn("provider tool exploded", result.quality_findings[0])
        self.assertIn("| agent_run:main_orchestrator | error |", metrics)

    def test_agent_fanout_runs_tasks_and_aggregates_metrics(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="main orchestrator")

        async def fake_runner(agent_id, _prompt, task_context, **_kwargs):
            await asyncio.sleep(0.01)
            return AgentRuntimeResult(
                agent_id=agent_id,
                final_output={
                    "agent_id": agent_id,
                    "run_id": task_context.run_id,
                    "status": "ready",
                    "summary": "This fake fanout result is long enough for a deterministic unit test.",
                    "memory_item_ids_used": list(task_context.memory_item_ids[:1]),
                },
                trace_id=task_context.trace_id,
                group_id=task_context.trace_group_id,
                quality_findings=[],
            )

        result = run_agent_fanout_sync(
            context,
            [
                AgentFanoutTask("news-aapl", "company_news_specialist", "company news specialist", "review AAPL"),
                AgentFanoutTask("news-msft", "company_news_specialist", "company news specialist", "review MSFT"),
            ],
            runner=fake_runner,
        )
        data = fanout_result_to_dict(result)

        self.assertEqual(result.status, "complete")
        self.assertEqual(len(result.results), 2)
        self.assertIn("fanout_task:news-aapl", [metric.name for metric in result.metrics])
        self.assertEqual(data["results"][0]["status"], "complete")

    def test_agent_fanout_preserves_partial_results_on_error(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="main orchestrator")

        async def mixed_runner(agent_id, prompt, task_context, **_kwargs):
            if "fail" in prompt:
                raise RuntimeError("specialist failed")
            return AgentRuntimeResult(
                agent_id=agent_id,
                final_output={
                    "agent_id": agent_id,
                    "run_id": task_context.run_id,
                    "status": "ready",
                    "summary": "This fake successful fanout result is long enough for a deterministic unit test.",
                    "memory_item_ids_used": list(task_context.memory_item_ids[:1]),
                },
                trace_id=task_context.trace_id,
                group_id=task_context.trace_group_id,
                quality_findings=[],
            )

        result = run_agent_fanout_sync(
            context,
            [
                AgentFanoutTask("ok", "company_news_specialist", "company news specialist", "succeed"),
                AgentFanoutTask("bad", "company_news_specialist", "company news specialist", "fail"),
            ],
            runner=mixed_runner,
        )

        self.assertEqual(result.status, "partial")
        self.assertEqual([item.status for item in result.results], ["complete", "error"])
        self.assertEqual(result.results[1].final_output["status"], "blocked")

    def test_agent_fanout_applies_per_task_timeout(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="main orchestrator")

        async def slow_runner(*_args, **_kwargs):
            await asyncio.sleep(0.2)
            raise AssertionError("timeout should cancel before this point")

        result = run_agent_fanout_sync(
            context,
            [AgentFanoutTask("slow", "company_news_specialist", "company news specialist", "slow", timeout_seconds=0.01)],
            runner=slow_runner,
        )

        self.assertEqual(result.status, "partial")
        self.assertEqual(result.results[0].status, "timeout")
        self.assertIn("timed out", result.results[0].quality_findings[0])

    def test_local_run_hooks_capture_tool_and_memory_metrics(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_runtime_test_repo(root)
            context = build_research_run_context(root=root, run_id="test_weekly", task="main orchestrator")
            telemetry = LocalRunTelemetry(context)
            hooks = LocalRunHooks(telemetry)
            wrapped_context = SimpleNamespace(context=context, tool_call_id="call-1")
            agent = SimpleNamespace(name="Main")
            tool = SimpleNamespace(name="load_repo_map")

            async def exercise_hooks():
                await hooks.on_agent_start(wrapped_context, agent)
                await hooks.on_tool_start(wrapped_context, agent, tool)
                await hooks.on_tool_end(wrapped_context, agent, tool, "tool result")
                await hooks.on_agent_end(wrapped_context, agent, {"status": "ready"})

            asyncio.run(exercise_hooks())

        metric_names = [metric.name for metric in telemetry.metrics]
        self.assertIn("memory_context:Main", metric_names)
        self.assertIn("tool:load_repo_map", metric_names)
        memory_metric = next(metric for metric in telemetry.metrics if metric.name == "memory_context:Main")
        self.assertEqual(memory_metric.memory_item_ids, context.memory_item_ids)

    def test_reported_memory_item_ids_includes_specialist_outputs(self):
        decision = OrchestratorDecision(
            agent_id="main_orchestrator",
            run_id="test_weekly",
            status="partial",
            summary="This is a sufficiently long summary about a partial run result with memory reporting.",
            memory_item_ids_used=["orch-1"],
        )
        decision.specialist_results.append(
            {
                "agent_id": "company_news_specialist",
                "status": "partial",
                "summary": "Specialist used memory.",
                "memory_item_ids_used": ["news-1", "orch-1"],
            }
        )

        self.assertEqual(reported_memory_item_ids(decision), ("orch-1", "news-1"))

    def test_agent_runtime_cli_smoke_does_not_call_model(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["--root", str(REPO_ROOT), "agent-runtime", "smoke", "--run-id", "test_weekly"])

        self.assertEqual(exit_code, 0)
        self.assertIn('"live_model_called": false', buffer.getvalue())

    def test_agent_runtime_cli_run_dry_run_does_not_call_model(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["--root", str(REPO_ROOT), "agent-runtime", "run", "--run-id", "test_weekly"])

        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn('"status": "dry_run"', output)
        self.assertIn('"live_model_called": false', output)
        self.assertIn("run_summary.md", output)

    def test_agent_runtime_cli_company_research_dry_run_uses_ticker_packet(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "--root",
                    str(REPO_ROOT),
                    "agent-runtime",
                    "run",
                    "--run-id",
                    "2026-05-09_weekly",
                    "--agent-id",
                    "company_research_orchestrator",
                    "--task",
                    "company research sub-orchestrator",
                    "--ticker",
                    "AAPL",
                ]
            )

        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn('"agent_id": "company_research_orchestrator"', output)
        self.assertIn("Company research packet", output)
        self.assertIn('\\"ticker\\": \\"AAPL\\"', output)

    def test_agent_runtime_cli_portfolio_review_dry_run_uses_packet(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "--root",
                    str(REPO_ROOT),
                    "agent-runtime",
                    "run",
                    "--run-id",
                    "2026-05-10_manual-market-energy-storage",
                    "--agent-id",
                    "portfolio_review_orchestrator",
                    "--task",
                    "portfolio review sub-orchestrator",
                ]
            )

        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn('"agent_id": "portfolio_review_orchestrator"', output)
        self.assertIn("Portfolio review packet", output)

    def test_agent_runtime_cli_memory_evaluation_dry_run_uses_packet(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "--root",
                    str(REPO_ROOT),
                    "agent-runtime",
                    "run",
                    "--run-id",
                    "2026-05-10_manual-market-energy-storage",
                    "--agent-id",
                    "memory_evaluation_orchestrator",
                    "--task",
                    "memory evaluation sub-orchestrator",
                ]
            )

        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn('"agent_id": "memory_evaluation_orchestrator"', output)
        self.assertIn("Memory evaluation packet", output)

    def test_agent_runtime_cli_validate_output(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "agents" / "runs" / "test_weekly"
            company_file = root / "stock_tracking" / "stock_info_files" / "monitoring" / "AAPL.md"
            memory_dir = root / "agents" / "memory"
            run_dir.mkdir(parents=True)
            company_file.parent.mkdir(parents=True)
            memory_dir.mkdir(parents=True)
            (root / "AGENTS.md").write_text("# Test agents\n", encoding="utf-8")
            company_file.write_text("# AAPL\n", encoding="utf-8")
            for name in (
                "README.md",
                "memory_index.md",
                "source_quality.md",
                "specialist_playbooks.md",
                "evaluation_metrics.md",
                "deprecated_memory.md",
            ):
                (memory_dir / name).write_text("# Test\n", encoding="utf-8")
            (memory_dir / "orchestrator_lessons.md").write_text(
                "\n".join(
                    [
                        "# Orchestrator Lessons",
                        "",
                        "- id: orch-test",
                        "- date: 2026-05-06",
                        "- type: procedural",
                        "- scope: orchestrator",
                        "- status: active",
                        "- confidence: high",
                        "- trigger/source: test",
                        "- lesson: Test lesson.",
                        "- use_when: Testing.",
                        "- do_not_use_when: Never.",
                        "- evidence: `tests/test_agent_runtime.py`",
                        "- owner: tests",
                        "- next_review: 2026-06-01",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "MEMORY.md").write_text("# Memory\n", encoding="utf-8")
            (run_dir / "agent_runtime_main_orchestrator.json").write_text(
                json.dumps(
                    {
                        "agent_id": "main_orchestrator",
                        "run_id": "test_weekly",
                        "status": "partial",
                        "summary": "This is a sufficiently long summary with a valid source-backed proposal and exact target file path.",
                        "memory_item_ids_used": ["orch-test"],
                        "specialist_results": [
                            {
                                "agent_id": "company_news_specialist",
                                "subject_type": "company",
                                "subject_id": "AAPL",
                                "status": "partial",
                                "summary": "Specialist result summary.",
                                "memory_item_ids_used": ["orch-test"],
                                "sources": [
                                    {
                                        "source_id": "source-1",
                                        "title": "Run report",
                                        "artifact_path": "agent_runtime_main_orchestrator.json",
                                    }
                                ],
                            }
                        ],
                        "file_update_proposals": [
                            {
                                "target_file": "stock_tracking/stock_info_files/monitoring/AAPL.md",
                                "update_type": "test",
                                "summary": "Update proposal.",
                                "source_ids": ["source-1"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(["--root", str(root), "agent-runtime", "validate-output", "--run-id", "test_weekly"])

        self.assertEqual(exit_code, 2)
        self.assertIn('"status": "needs_review"', buffer.getvalue())

    def test_orchestrator_input_names_required_artifacts(self):
        prompt = build_orchestrator_input("test_weekly")

        self.assertIn("run_summary.md", prompt)
        self.assertIn("quality_report.md", prompt)
        self.assertIn("listing evidence packets", prompt)
        self.assertIn("company_research/*.md", prompt)
        self.assertIn("memory_evaluation/*.md", prompt)

    def test_main_orchestrator_input_packet_aggregates_sub_orchestrator_reports(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_runtime_test_repo(root)
            write_portfolio_review_test_artifacts(root)
            write_memory_evaluation_test_artifacts(root)
            run_dir = root / "agents" / "runs" / "test_weekly"
            (run_dir / "company_research").mkdir(parents=True, exist_ok=True)
            (run_dir / "company_research" / "AAPL_company_research.md").write_text("# Company Research\n", encoding="utf-8")
            (run_dir / "market_research" / "theme_market_research.md").write_text("# Market Research\n", encoding="utf-8")
            (run_dir / "portfolio_review").mkdir(parents=True, exist_ok=True)
            (run_dir / "portfolio_review" / "portfolio_review.md").write_text("# Portfolio Review\n", encoding="utf-8")
            (run_dir / "memory_evaluation").mkdir(parents=True, exist_ok=True)
            (run_dir / "memory_evaluation" / "memory_evaluation.md").write_text("# Memory Evaluation\n", encoding="utf-8")
            (root / "agents" / "human_review_digest.md").write_text("# Digest\n", encoding="utf-8")
            context = build_research_run_context(root=root, run_id="test_weekly", task="main orchestrator")

            packet = build_main_orchestrator_input_packet(context, provider_mode="execute", analysis_mode="execute")
            prompt = build_orchestrator_input("test_weekly", context.memory_item_ids, context=context)

        self.assertIn("agents/runs/test_weekly/company_research/AAPL_company_research.md", packet.company_research_reports)
        self.assertIn("agents/runs/test_weekly/market_research/candidate_verification_result.md", packet.candidate_verification_results)
        self.assertIn("agents/runs/test_weekly/portfolio_review/portfolio_review.md", packet.portfolio_review_reports)
        self.assertIn("agents/runs/test_weekly/memory_evaluation/memory_evaluation.md", packet.memory_evaluation_reports)
        self.assertEqual(packet.open_human_review_count, 1)
        self.assertIn("Main aggregation packet", prompt)

    def test_output_quality_flags_short_summary(self):
        decision = OrchestratorDecision(
            agent_id="main_orchestrator",
            run_id="test_weekly",
            status="ready",
            summary="Too short.",
        )

        findings = evaluate_runtime_output_quality(decision)

        self.assertTrue(any("Summary is too short" in finding for finding in findings))

    def test_output_quality_flags_missing_target_file(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="main orchestrator")
        decision = OrchestratorDecision(
            agent_id="main_orchestrator",
            run_id="test_weekly",
            status="partial",
            summary="This is a sufficiently long summary about a partial run result with a bad target file path.",
            memory_item_ids_used=["orch-2026-05-06-openai-agents-sdk-selected"],
        )
        decision.file_update_proposals.append(
            {
                "target_file": "companies/AAPL.md",
                "update_type": "news",
                "summary": "Bad target path.",
            }
        )

        findings = evaluate_runtime_output_quality(decision, context)

        self.assertTrue(any("target does not exist" in finding for finding in findings))

    def test_output_quality_flags_unknown_memory_id(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="main orchestrator")
        decision = OrchestratorDecision(
            agent_id="main_orchestrator",
            run_id="test_weekly",
            status="partial",
            summary="This is a sufficiently long summary about a partial run result with an invalid memory id.",
            memory_item_ids_used=["agents/memory/orchestrator_lessons.md"],
        )

        findings = evaluate_runtime_output_quality(decision, context)

        self.assertTrue(any("unknown operational memory item ids" in finding for finding in findings))

    def test_output_quality_flags_unknown_proposal_source_id(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="main orchestrator")
        decision = OrchestratorDecision(
            agent_id="main_orchestrator",
            run_id="test_weekly",
            status="partial",
            summary="This is a sufficiently long summary about a partial run result with an unknown proposal source id.",
            memory_item_ids_used=["orch-2026-05-06-openai-agents-sdk-selected"],
        )
        decision.file_update_proposals.append(
            {
                "target_file": "stock_tracking/stock_info_files/monitoring/AAPL.md",
                "update_type": "news",
                "summary": "Unknown source id.",
                "source_ids": ["missing-source-id"],
            }
        )

        findings = evaluate_runtime_output_quality(decision, context)

        self.assertTrue(any("references unknown source_ids" in finding for finding in findings))

    def test_output_to_dict_serializes_dataclass(self):
        decision = OrchestratorDecision(
            agent_id="main_orchestrator",
            run_id="test_weekly",
            status="partial",
            summary="This is a sufficiently long summary about a partial run result with evidence gaps.",
            memory_item_ids_used=["orch-2026-05-06-openai-agents-sdk-selected"],
        )

        data = output_to_dict(decision)

        self.assertEqual(data["agent_id"], "main_orchestrator")
        self.assertEqual(data["memory_item_ids_used"], ["orch-2026-05-06-openai-agents-sdk-selected"])


if __name__ == "__main__":
    unittest.main()
