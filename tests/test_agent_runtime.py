from pathlib import Path
from contextlib import redirect_stdout
import io
import unittest

from agents import Agent

from stock_research.agent_runtime.context import build_research_run_context
from stock_research.agent_runtime.registry import build_agent, build_agent_tool, list_agent_specs
from stock_research.agent_runtime.runner import build_run_config
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

    def test_main_orchestrator_exposes_company_news_specialist_as_tool(self):
        context = build_research_run_context(root=REPO_ROOT, run_id="test_weekly", task="main orchestrator")
        agent = build_agent("main_orchestrator", context)
        tool_names = {getattr(tool, "name", type(tool).__name__) for tool in agent.tools}

        self.assertIsInstance(agent, Agent)
        self.assertIn("load_run_markdown", tool_names)
        self.assertIn("load_operational_memory", tool_names)
        self.assertIn("company_news_specialist", tool_names)

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


if __name__ == "__main__":
    unittest.main()
