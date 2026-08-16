from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import date
import json
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
import io

from stock_research.agent_runtime.context import build_research_run_context
from stock_research.agent_runtime.runner import build_run_config
from stock_research.cli import main
from stock_research.market_research_runner import build_manual_market_manifest
from stock_research.model_routing import resolve_model_for_route
from stock_research.providers.xai_grok import XaiGrokError


def write_routing_test_repo(root: Path) -> None:
    (root / "AGENTS.md").write_text("# Test agents\n", encoding="utf-8")
    (root / "stock_tracking").mkdir()
    routing_dir = root / "agents"
    routing_dir.mkdir()
    (routing_dir / "model_routing.yaml").write_text(
        "\n".join(
            [
                "defaults:",
                "  openai_strong: gpt-5.5",
                "  openai_balanced: gpt-5.4-mini",
                "  openai_fast: gpt-5.4-mini",
                "  openai_nano: gpt-5.4-mini",
                "  xai_grok_x_search: grok-4.6",
                "  codex_manual_model: gpt-5.5",
                "  codex_manual_reasoning: high",
                "routes:",
                "  main_orchestrator:",
                "    provider: openai",
                "    model_tier: strong",
                "    complexity: high",
                "    codex_preferred_when_manual: true",
                "  writer_specialist:",
                "    provider: openai",
                "    model_tier: fast",
                "    complexity: low_medium",
                "  xai_stock_sentiment:",
                "    provider: xai",
                "    model_tier: grok_x_search",
                "    complexity: high",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


class ModelRoutingTests(unittest.TestCase):
    def test_strong_routes_use_gpt_55_and_codex_manual_preference(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_routing_test_repo(root)

            route = resolve_model_for_route(root, "main_orchestrator")

        self.assertEqual(route.model, "gpt-5.5")
        self.assertEqual(route.provider, "openai")
        self.assertEqual(route.model_tier, "strong")
        self.assertTrue(route.codex_preferred_when_manual)
        self.assertEqual(route.codex_manual_model, "gpt-5.5")
        self.assertEqual(route.codex_manual_reasoning, "high")

    def test_fast_routes_use_configured_fast_tier(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_routing_test_repo(root)

            route = resolve_model_for_route(root, "writer_specialist")

        self.assertEqual(route.model, "gpt-5.4-mini")
        self.assertEqual(route.model_tier, "fast")

    def test_explicit_and_env_overrides_win_over_config(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_routing_test_repo(root)
            explicit = resolve_model_for_route(root, "main_orchestrator", explicit_model="override-model")
            with patch.dict(os.environ, {"STOCK_RESEARCH_MODEL_MAIN_ORCHESTRATOR": "route-env-model"}):
                route_env = resolve_model_for_route(root, "main_orchestrator")
            with patch.dict(os.environ, {"STOCK_RESEARCH_OPENAI_FAST_MODEL": "fast-env-model"}):
                tier_env = resolve_model_for_route(root, "writer_specialist")

        self.assertEqual(explicit.model, "override-model")
        self.assertEqual(explicit.source, "explicit")
        self.assertEqual(route_env.model, "route-env-model")
        self.assertEqual(tier_env.model, "fast-env-model")

    def test_legacy_gpt_41_override_is_blocked(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_routing_test_repo(root)

            with patch.dict(os.environ, {"STOCK_RESEARCH_OPENAI_FAST_MODEL": "gpt-4.1-2025-04-14"}):
                with self.assertRaisesRegex(ValueError, "blocked legacy model"):
                    resolve_model_for_route(root, "writer_specialist")

    def test_xai_routes_use_grok_x_search_tier(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_routing_test_repo(root)

            route = resolve_model_for_route(root, "xai_stock_sentiment")

        self.assertEqual(route.provider, "xai")
        self.assertEqual(route.model, "grok-4.6")
        self.assertEqual(route.complexity, "high")

    def test_missing_config_uses_safe_defaults(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "AGENTS.md").write_text("# Test agents\n", encoding="utf-8")
            (root / "stock_tracking").mkdir()

            strong = resolve_model_for_route(root, "main_orchestrator")
            fast = resolve_model_for_route(root, "writer_specialist")

        self.assertEqual(strong.model, "gpt-5.5")
        self.assertEqual(strong.source, "built_in")
        self.assertEqual(fast.model, "gpt-5.4-mini")
        self.assertEqual(fast.source, "built_in")

    def test_run_config_uses_route_when_no_explicit_model(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_routing_test_repo(root)
            context = build_research_run_context(root=root, run_id="test_weekly", task="main orchestrator")

            run_config = build_run_config(context, agent_id="main_orchestrator")

        self.assertEqual(run_config.model, "gpt-5.5")

    def test_manual_market_manifest_uses_xai_routing_override(self):
        with patch.dict(os.environ, {"STOCK_RESEARCH_XAI_GROK_MODEL": "grok-routing-test"}):
            manifest = build_manual_market_manifest(
                topic="AI semiconductor supply chain",
                subject_type="industry",
                subject_id="ai_semiconductor_supply_chain",
                run_id="test_manual_market",
                current_date=date(2026, 5, 15),
            )

        xai_tasks = [task for task in manifest["provider_tasks"] if task["provider"] == "xai_grok"]
        self.assertEqual(len(xai_tasks), 1)
        self.assertEqual(xai_tasks[0]["args"]["model"], "grok-routing-test")

    def test_cli_model_routing_show(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_routing_test_repo(root)
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(["--root", str(root), "model-routing", "show", "--route", "main_orchestrator"])

        self.assertEqual(exit_code, 0)
        data = json.loads(buffer.getvalue())
        self.assertEqual(data["model"], "gpt-5.5")
        self.assertEqual(data["model_tier"], "strong")

    def test_cli_xai_models_fails_closed_when_catalog_resolution_fails(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_routing_test_repo(root)
            buffer = io.StringIO()
            with (
                patch("stock_research.cli.resolve_xai_api_key", return_value="test-key"),
                patch(
                    "stock_research.cli.resolve_available_xai_search_model",
                    side_effect=XaiGrokError("No compatible Grok search model is available."),
                ),
                redirect_stdout(buffer),
            ):
                exit_code = main(["--root", str(root), "xai", "models"])

        self.assertEqual(exit_code, 1)
        self.assertIn("No compatible Grok search model is available", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
