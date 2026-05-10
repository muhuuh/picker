from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.memory import (
    add_memory_item,
    build_memory_context,
    deprecate_memory_item,
    format_memory_context_for_prompt,
    load_memory_state,
    memory_summary,
    validate_memory_state,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class MemoryTests(unittest.TestCase):
    def test_memory_state_loads_seeded_items(self):
        memory = load_memory_state(REPO_ROOT)
        summary = memory_summary(memory)

        self.assertGreaterEqual(summary["total_items"], 8)
        self.assertTrue(summary["files"]["memory_index.md"]["exists"])
        self.assertGreater(summary["files"]["source_quality.md"]["items"], 0)

    def test_memory_validation_passes_current_files(self):
        memory = load_memory_state(REPO_ROOT)
        report = validate_memory_state(memory)

        self.assertTrue(report.ok, report.errors)

    def test_financial_context_loads_source_quality_and_playbooks(self):
        memory = load_memory_state(REPO_ROOT)
        context = build_memory_context(memory, "financial specialist")

        self.assertIn("agents/memory/source_quality.md", context["memory_files"])
        self.assertIn("agents/memory/specialist_playbooks.md", context["memory_files"])
        self.assertTrue(any(item["scope"] == "financial" for item in context["active_items"]))

    def test_sentiment_context_includes_deprecated_memory(self):
        memory = load_memory_state(REPO_ROOT)
        context = build_memory_context(memory, "sentiment")

        self.assertIn("agents/memory/deprecated_memory.md", context["memory_files"])
        self.assertTrue(any(item["status"] == "deprecated" for item in context["active_items"]))

    def test_sdk_tool_guardrail_context_includes_orchestrator_lessons(self):
        memory = load_memory_state(REPO_ROOT)
        context = build_memory_context(memory, "sdk provider analysis tool guardrails")

        self.assertIn("agents/memory/orchestrator_lessons.md", context["memory_files"])
        self.assertIn("agents/memory/source_quality.md", context["memory_files"])
        self.assertTrue(any(item["id"] == "orch-2026-05-07-guarded-sdk-provider-analysis-tools" for item in context["active_items"]))

    def test_prompt_context_formats_task_relevant_lessons(self):
        memory = load_memory_state(REPO_ROOT)
        prompt_context = format_memory_context_for_prompt(memory, "news specialist", max_items=5)

        self.assertIn("Operational Memory Context", prompt_context)
        self.assertIn("Use these lessons as constraints", prompt_context)
        self.assertIn("agents/memory/source_quality.md", prompt_context)

    def test_add_memory_item_writes_schema_valid_item(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_memory_repo(Path(temp_dir))

            result = add_memory_item(
                root=root,
                current_date=None,
                memory_file="source_quality.md",
                fields={
                    "id": "source-test-item",
                    "date": "2026-05-04",
                    "type": "source_quality",
                    "scope": "provider",
                    "status": "active",
                    "confidence": "high",
                    "trigger/source": "unit test",
                    "lesson": "Test provider lesson.",
                    "use_when": "Testing memory writes.",
                    "do_not_use_when": "Outside tests.",
                    "evidence": "`tests/test_memory.py`",
                    "owner": "memory tests",
                    "next_review": "2026-06-01",
                },
            )
            memory = load_memory_state(root)
            report = validate_memory_state(memory)

            self.assertEqual(result.item_id, "source-test-item")
            self.assertTrue(report.ok, report.errors)
            self.assertIn("source-test-item", (root / "agents/memory/source_quality.md").read_text(encoding="utf-8"))

    def test_deprecate_memory_item_marks_original_and_records_deprecation(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_memory_repo(Path(temp_dir))
            add_memory_item(
                root=root,
                current_date=None,
                memory_file="orchestrator_lessons.md",
                fields={
                    "id": "orch-test-old-path",
                    "date": "2026-05-04",
                    "type": "procedural",
                    "scope": "orchestrator",
                    "status": "active",
                    "confidence": "medium",
                    "trigger/source": "unit test",
                    "lesson": "Old path should be deprecated.",
                    "use_when": "Testing deprecation.",
                    "do_not_use_when": "After deprecation.",
                    "evidence": "`tests/test_memory.py`",
                    "owner": "memory tests",
                    "next_review": "2026-06-01",
                },
            )

            result = deprecate_memory_item(
                root=root,
                item_id="orch-test-old-path",
                reason="unit test correction",
                replacement="Use the new path.",
            )
            memory = load_memory_state(root)
            report = validate_memory_state(memory)
            original = [item for item in memory.items if item.fields["id"] == "orch-test-old-path"][0]

            self.assertEqual(result.action, "deprecated")
            self.assertEqual(original.fields["status"], "deprecated")
            self.assertTrue(report.ok, report.errors)
            self.assertIn("unit test correction", (root / "agents/memory/deprecated_memory.md").read_text(encoding="utf-8"))

def seed_memory_repo(root: Path) -> Path:
    (root / "stock_tracking").mkdir(parents=True)
    (root / "agents/memory").mkdir(parents=True)
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    for name in [
        "README.md",
        "memory_index.md",
        "orchestrator_lessons.md",
        "source_quality.md",
        "specialist_playbooks.md",
        "evaluation_metrics.md",
        "deprecated_memory.md",
    ]:
        title = name.replace("_", " ").replace(".md", "").title()
        (root / "agents/memory" / name).write_text(f"# {title}\n", encoding="utf-8")
    return root


if __name__ == "__main__":
    unittest.main()
