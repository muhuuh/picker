from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.human import append_human_request, classify_request
from stock_research.manifest import build_weekly_manifest, next_saturday
from stock_research.repo import load_repo_state
from stock_research.validation import validate_repo_state


REPO_ROOT = Path(__file__).resolve().parents[1]


class StockResearchCoreTests(unittest.TestCase):
    def test_repo_validates_current_scaffold(self):
        state = load_repo_state(REPO_ROOT)
        report = validate_repo_state(state, date(2026, 5, 3))

        self.assertTrue(report.ok, report.errors)

    def test_manifest_uses_next_saturday_and_research_priorities(self):
        state = load_repo_state(REPO_ROOT)
        manifest = build_weekly_manifest(state, date(2026, 5, 3))

        self.assertEqual(manifest["run_date"], "2026-05-09")
        self.assertEqual(manifest["scope"], ["US", "Europe"])
        self.assertEqual(len(manifest["inputs"]["research_priorities"]), 1)

    def test_next_saturday_returns_same_day_when_today_is_saturday(self):
        self.assertEqual(next_saturday(date(2026, 5, 9)), date(2026, 5, 9))

    def test_classify_stock_request_extracts_tickers(self):
        result = classify_request("Research ASML, TSM, AMD, and SAP")

        self.assertEqual(result.request_type, "stock_research")
        self.assertEqual(result.tickers, ["AMD", "ASML", "SAP", "TSM"])
        self.assertEqual(result.next_run, "yes")

    def test_append_human_request_adds_next_id(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queue = root / "docs" / "plans"
            queue.mkdir(parents=True)
            (queue / "human_research_requests.md").write_text(
                """# Human Research Requests

| ID | Date Added | Request | Type | Priority | Status | Tickers | Industries / Themes | Target Files | Next Run | Immediate Action | Owner / Agent | Result Link | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HIR-0001 | 2026-05-03 | Existing | other | low | done |  |  |  | no | no | Codex |  |  |
""",
                encoding="utf-8",
            )

            request_id = append_human_request(root, "Research ASML and AMD", today=date(2026, 5, 3))
            text = (queue / "human_research_requests.md").read_text(encoding="utf-8")

            self.assertEqual(request_id, "HIR-0002")
            self.assertIn("Research ASML and AMD", text)
            self.assertIn("HIR-0002", text)


if __name__ == "__main__":
    unittest.main()
