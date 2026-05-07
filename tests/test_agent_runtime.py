from pathlib import Path
from contextlib import redirect_stdout
import io
import json
from tempfile import TemporaryDirectory
import unittest

from agents import Agent

from stock_research.agent_runtime.context import build_research_run_context
from stock_research.agent_runtime.outputs import OrchestratorDecision
from stock_research.agent_runtime.reports import build_orchestrator_input, evaluate_runtime_output_quality, output_to_dict
from stock_research.agent_runtime.registry import build_agent, build_agent_tool, list_agent_specs
from stock_research.agent_runtime.runner import build_run_config
from stock_research.agent_runtime.tools.repo_tools import list_evidence_packets_data, load_memory_prompt_context_for_task
from stock_research.cli import main


REPO_ROOT = Path(__file__).resolve().parents[1]


class AgentRuntimeTests(unittest.TestCase):
    def test_registry_lists_orchestrator_and_specialist(self):
        specs = {spec.agent_id: spec for spec in list_agent_specs()}

        self.assertEqual(specs["main_orchestrator"].role, "orchestrator")
        self.assertEqual(specs["company_news_specialist"].role, "specialist")

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
        self.assertIn("load_stock_tracking_csv", tool_names)
        self.assertIn("company_news_specialist", tool_names)

    def test_company_news_context_uses_specialist_memory(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="company news specialist")

        self.assertIn("memory-2026-05-04-company-news-specialist-review-is-implemented", context.memory_item_ids)
        self.assertIn("Company-news specialist review is implemented", context.memory_context)

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

    def test_specialist_can_be_built_as_tool(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="company news specialist")
        tool = build_agent_tool("company_news_specialist", context)

        self.assertEqual(getattr(tool, "name", ""), "company_news_specialist")

    def test_run_config_uses_trace_metadata_without_sensitive_data(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="main orchestrator")
        run_config = build_run_config(context, model="gpt-5.5")

        self.assertEqual(run_config.model, "gpt-5.5")
        self.assertEqual(run_config.workflow_name, "stock-research-agent-runtime")
        self.assertEqual(run_config.trace_id, context.trace_id)
        self.assertFalse(run_config.trace_include_sensitive_data)
        self.assertEqual(run_config.trace_metadata["run_id"], "test_weekly")

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
        self.assertIn("reports/company_news_specialist", prompt)

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
