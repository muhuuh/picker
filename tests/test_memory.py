from pathlib import Path
import unittest

from stock_research.memory import build_memory_context, load_memory_state, memory_summary, validate_memory_state


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


if __name__ == "__main__":
    unittest.main()
