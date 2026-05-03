from datetime import date
from pathlib import Path
import unittest

from stock_research.provider_runner import run_provider_tasks


class ProviderRunnerTests(unittest.TestCase):
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


def provider_task(task_id: str, provider: str):
    return {
        "id": task_id,
        "provider": provider,
        "tool": "search" if provider == "exa" else "company",
        "subject_type": "theme",
        "subject_id": "test",
        "priority": "medium",
        "args": {"query": "test", "run_id": "2026-05-09_weekly"},
        "reason": "test",
    }


def fake_executor(root: Path, task: dict, current_date: date | None):
    return {"packet_id": f"packet_{task['id']}", "paths": [str(root / "packet.json")]}


if __name__ == "__main__":
    unittest.main()
