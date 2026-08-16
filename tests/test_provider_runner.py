from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from stock_research.provider_runner import execute_provider_task, run_provider_tasks
from stock_research.providers.xai_grok import XaiModelCatalog, XaiModelResolution


class ProviderRunnerTests(unittest.TestCase):
    def test_xai_task_resolves_authenticated_model_and_passes_provenance(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            task = {
                "id": "xai_stock_aapl",
                "provider": "xai_grok",
                "tool": "x_search",
                "subject_type": "company",
                "subject_id": "AAPL",
                "args": {
                    "prompt": "Search X for AAPL discussion.",
                    "run_id": "2026-08-16_test",
                    "research_kind": "stock_sentiment",
                    "model": "grok-4.6",
                    "reasoning_effort": "high",
                },
            }
            resolution = XaiModelResolution(
                requested_model="grok-4.6",
                resolved_model="grok-4.6",
                source="authenticated_model_catalog",
            )
            catalog = XaiModelCatalog(model_ids=("grok-4.6",), aliases=())
            with (
                patch("stock_research.provider_runner.resolve_xai_api_key", return_value="test-key"),
                patch(
                    "stock_research.provider_runner.resolve_available_xai_search_model",
                    return_value=(resolution, catalog),
                ) as resolve_model,
                patch(
                    "stock_research.provider_runner.build_xai_x_search_packet",
                    return_value=(SimpleNamespace(packet_id="packet-1"), [root / "packet.json", root / "raw.json"]),
                ) as build_packet,
            ):
                result = execute_provider_task(root, task, current_date=date(2026, 8, 16))

        resolve_model.assert_called_once_with("grok-4.6", "test-key")
        options = build_packet.call_args.kwargs["options"]
        self.assertEqual(options.requested_model, "grok-4.6")
        self.assertEqual(options.model, "grok-4.6")
        self.assertEqual(options.model_resolution_source, "authenticated_model_catalog")
        self.assertEqual(options.reasoning_effort, "high")
        self.assertEqual(result["packet_id"], "packet-1")

    def test_provider_runner_dry_run_filters_provider_and_limit(self):
        manifest = {
            "manifest_id": "weekly_2026-05-09",
            "provider_tasks": [
                provider_task("exa_one", "exa"),
                provider_task("yfinance_one", "yfinance"),
                provider_task("exa_two", "exa"),
            ],
        }

        result = run_provider_tasks(
            root=Path("."),
            manifest=manifest,
            execute=False,
            providers={"exa"},
            limit=1,
        )

        self.assertEqual(result["mode"], "dry_run")
        self.assertEqual(result["planned_count"], 1)
        self.assertEqual(result["planned"][0]["id"], "exa_one")

    def test_provider_runner_execute_uses_injected_executor(self):
        manifest = {"manifest_id": "weekly_2026-05-09", "provider_tasks": [provider_task("exa_one", "exa")]}

        result = run_provider_tasks(
            root=Path("."),
            manifest=manifest,
            execute=True,
            current_date=date(2026, 5, 3),
            executor=fake_executor,
        )

        self.assertEqual(result["mode"], "execute")
        self.assertEqual(result["executed"][0]["packet_id"], "packet_exa_one")
        self.assertEqual(result["errors"], [])

    def test_execute_fmp_provider_task_passes_fallback_key_from_env_file(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env").write_text("FMP_API_KEY=primary\nFMP_API_KEY2=secondary\n", encoding="utf-8")

            def fake_build_fmp_company_packet(**kwargs):
                self.assertEqual(kwargs["api_key"], "primary")
                self.assertEqual(kwargs["fallback_api_key"], "secondary")
                return SimpleNamespace(packet_id="fmp_packet"), [root / "packet.json"]

            with patch("stock_research.provider_runner.build_fmp_company_packet", side_effect=fake_build_fmp_company_packet):
                result = execute_provider_task(root, provider_task("fmp_one", "fmp"), current_date=date(2026, 5, 16))

            self.assertEqual(result["packet_id"], "fmp_packet")

    def test_execute_alpha_provider_task_passes_fallback_key_from_env_file(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env").write_text(
                "ALPHA_VANTAGE_API_KEY=primary\nALPHA_VANTAGE_API_KEY2=secondary\n",
                encoding="utf-8",
            )

            def fake_build_alpha_vantage_company_packet(**kwargs):
                self.assertEqual(kwargs["api_key"], "primary")
                self.assertEqual(kwargs["fallback_api_key"], "secondary")
                return SimpleNamespace(packet_id="alpha_packet"), [root / "packet.json"]

            with patch(
                "stock_research.provider_runner.build_alpha_vantage_company_packet",
                side_effect=fake_build_alpha_vantage_company_packet,
            ):
                result = execute_provider_task(root, provider_task("alpha_one", "alpha_vantage"), current_date=date(2026, 5, 16))

            self.assertEqual(result["packet_id"], "alpha_packet")


def provider_task(task_id: str, provider: str):
    return {
        "id": task_id,
        "provider": provider,
        "tool": "search" if provider == "exa" else "company",
        "subject_type": "theme",
        "subject_id": "test",
        "priority": "medium",
        "args": {"query": "test", "ticker": "AAPL", "run_id": "2026-05-09_weekly"},
        "reason": "test",
    }


def fake_executor(root: Path, task: dict, current_date: date | None):
    return {"packet_id": f"packet_{task['id']}", "paths": [str(root / "packet.json")]}


if __name__ == "__main__":
    unittest.main()
