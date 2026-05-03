from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import csv
import unittest

from stock_research.router import route_request


class RequestRouterTests(unittest.TestCase):
    def test_stock_request_adds_monitoring_rows_and_company_files(self):
        with TemporaryDirectory() as temp_dir:
            root = create_routing_scaffold(Path(temp_dir))

            result = route_request(root, "Research ASML and AMD", priority="high", today=date(2026, 5, 3))

            self.assertEqual(result.request_type, "stock_research")
            rows = read_csv(root / "stock_tracking" / "monitoring" / "monitoring.csv")
            self.assertEqual([row["ticker"] for row in rows], ["AMD", "ASML"])
            self.assertTrue((root / "stock_tracking" / "stock_info_files" / "monitoring" / "AMD_pending.md").exists())
            self.assertTrue((root / "stock_tracking" / "stock_info_files" / "monitoring" / "ASML_pending.md").exists())

    def test_industry_request_creates_research_file_and_priority(self):
        with TemporaryDirectory() as temp_dir:
            root = create_routing_scaffold(Path(temp_dir))

            result = route_request(
                root,
                "Look into European grid infrastructure suppliers",
                priority="high",
                today=date(2026, 5, 3),
            )

            self.assertEqual(result.request_type, "industry_research")
            self.assertTrue((root / "market_research" / "industries" / "european_grid_infrastructure_suppliers.md").exists())
            priorities = (root / "strategy" / "research_priorities.md").read_text(encoding="utf-8")
            self.assertIn("RP-0002", priorities)
            self.assertIn("European Grid Infrastructure Suppliers", priorities)

    def test_strategy_request_adds_review_item(self):
        with TemporaryDirectory() as temp_dir:
            root = create_routing_scaffold(Path(temp_dir))

            result = route_request(root, "From now on, avoid companies with heavy dilution", today=date(2026, 5, 3))

            self.assertEqual(result.request_type, "strategy_change")
            self.assertIn("strategy change approval", result.review_items)
            review_queue = (root / "agents" / "human_review_queue.md").read_text(encoding="utf-8")
            self.assertIn("HRQ-0002", review_queue)
            self.assertIn("heavy dilution", review_queue)

    def test_manual_request_creates_manual_manifest(self):
        with TemporaryDirectory() as temp_dir:
            root = create_routing_scaffold(Path(temp_dir))

            result = route_request(root, "Run research now for ASML", today=date(2026, 5, 3))

            self.assertIn(result.request_type, {"stock_research", "manual_run"})
            if result.request_type == "manual_run":
                self.assertTrue((root / "agents" / "runs" / "2026-05-03_manual-hir-0002" / "manifest.json").exists())


def create_routing_scaffold(root: Path) -> Path:
    (root / "docs" / "plans").mkdir(parents=True)
    (root / "strategy").mkdir()
    (root / "agents").mkdir()
    (root / "market_research" / "industries").mkdir(parents=True)
    (root / "market_research" / "themes").mkdir(parents=True)
    (root / "stock_tracking" / "monitoring").mkdir(parents=True)
    (root / "stock_tracking" / "stock_info_files" / "monitoring").mkdir(parents=True)

    (root / "docs" / "plans" / "human_research_requests.md").write_text(
        """# Human Research Requests

| ID | Date Added | Request | Type | Priority | Status | Tickers | Industries / Themes | Target Files | Next Run | Immediate Action | Owner / Agent | Result Link | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HIR-0001 | 2026-05-03 | Existing | other | low | done |  |  |  | no | no | Codex |  |  |
""",
        encoding="utf-8",
    )
    (root / "strategy" / "research_priorities.md").write_text(
        """# Research Priorities

| Priority ID | Topic | Type | Geography | Priority | Status | Why It Matters | Research Cadence | Last Reviewed | Next Review | Related Files | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RP-0001 | US and Europe stock discovery | geography | US, Europe | high | active | Scope. | weekly | 2026-05-03 | 2026-05-09 | docs |  |
""",
        encoding="utf-8",
    )
    (root / "agents" / "human_review_queue.md").write_text(
        """# Human Review Queue

| ID | Date Added | Item | Decision Needed | Priority | Status | Related Files | Evidence / Run Link | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HRQ-0001 | 2026-05-03 | Existing | Decide. | low | open |  |  |  |
""",
        encoding="utf-8",
    )
    (root / "strategy" / "investment_strategy.md").write_text("# Investment Strategy\n", encoding="utf-8")
    (root / "stock_tracking" / "monitoring" / "monitoring.csv").write_text(
        "ticker,company_name,exchange,country,currency,sector,industry,status,stock_info_file,source,price,market_cap,pe_ratio,date_found,date_last_updated,next_review_date,last_filing_checked,last_news_checked,last_sentiment_checked,alert_level,watch_reason,target_entry_criteria,notes\n",
        encoding="utf-8",
    )
    return root


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
