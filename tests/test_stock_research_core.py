from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.human import append_human_request, classify_request
from stock_research.manifest import build_weekly_manifest, next_saturday
from stock_research.repo import CsvTable, RepoState, load_repo_state
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
        self.assertIn("provider_tasks", manifest)
        self.assertIn("analysis_tasks", manifest)

    def test_manifest_plans_default_provider_tasks_for_tracked_tickers(self):
        state = repo_state_for_manifest(
            current_rows=[
                {
                    "ticker": "AAPL",
                    "company_name": "Apple Inc.",
                    "exchange": "NASDAQ",
                    "country": "US",
                }
            ],
            monitoring_rows=[
                {
                    "ticker": "ASML",
                    "company_name": "ASML Holding",
                    "exchange": "Euronext Amsterdam",
                    "country": "Netherlands",
                }
            ],
        )
        manifest = build_weekly_manifest(state, date(2026, 5, 3))
        task_ids = {task["id"] for task in manifest["provider_tasks"]}
        analysis_task_ids = {task["id"] for task in manifest["analysis_tasks"]}

        self.assertIn("yfinance_company_aapl", task_ids)
        self.assertIn("fmp_company_aapl", task_ids)
        self.assertIn("alpha_vantage_company_aapl", task_ids)
        self.assertIn("polygon_company_aapl", task_ids)
        self.assertIn("sec_company_aapl", task_ids)
        self.assertIn("exa_news_company_aapl", task_ids)
        self.assertIn("xai_x_search_company_aapl", task_ids)
        self.assertIn("yfinance_company_asml", task_ids)
        self.assertIn("fmp_company_asml", task_ids)
        self.assertIn("alpha_vantage_company_asml", task_ids)
        self.assertIn("exa_news_company_asml", task_ids)
        self.assertIn("xai_x_search_company_asml", task_ids)
        self.assertNotIn("polygon_company_asml", task_ids)
        self.assertNotIn("sec_company_asml", task_ids)
        self.assertIn("financial_compare_aapl", analysis_task_ids)
        self.assertIn("financial_compare_asml", analysis_task_ids)
        self.assertIn("financial_review_aapl", analysis_task_ids)
        self.assertIn("financial_review_asml", analysis_task_ids)

    def test_manifest_routes_research_priorities_and_human_requests_to_exa_modes(self):
        state = repo_state_for_manifest(
            priorities=[
                {
                    "Topic": "European grid infrastructure",
                    "Type": "industry",
                    "Geography": "Europe",
                    "Priority": "high",
                    "Status": "active",
                    "Why It Matters": "Electrification bottleneck",
                }
            ],
            human_requests=[
                {
                    "ID": "HIR-0099",
                    "Request": "Research robotics suppliers",
                    "Type": "industry_research",
                    "Priority": "high",
                    "Status": "queued_for_weekly_run",
                    "Tickers": "",
                    "Industries / Themes": "robotics suppliers",
                    "Next Run": "yes",
                },
                {
                    "ID": "HIR-0100",
                    "Request": "Research AMD",
                    "Type": "stock_research",
                    "Priority": "medium",
                    "Status": "queued_for_weekly_run",
                    "Tickers": "AMD",
                    "Industries / Themes": "",
                    "Next Run": "yes",
                },
            ],
        )
        manifest = build_weekly_manifest(state, date(2026, 5, 3))
        tasks = {task["id"]: task for task in manifest["provider_tasks"]}
        analysis_tasks = {task["id"]: task for task in manifest["analysis_tasks"]}

        self.assertEqual(tasks["exa_research_priority_european_grid_infrastructure"]["args"]["mode"], "industry")
        self.assertEqual(tasks["exa_discovery_priority_european_grid_infrastructure"]["args"]["mode"], "company")
        self.assertEqual(tasks["exa_human_hir_0099_industry_robotics_suppliers"]["args"]["mode"], "industry")
        self.assertEqual(tasks["exa_human_hir_0099_company_robotics_suppliers"]["args"]["mode"], "company")
        self.assertEqual(tasks["exa_human_hir_0100_news_amd"]["args"]["mode"], "news")
        self.assertEqual(tasks["fmp_human_hir_0100_company_amd"]["provider"], "fmp")
        self.assertEqual(tasks["alpha_vantage_human_hir_0100_company_amd"]["provider"], "alpha_vantage")
        self.assertEqual(tasks["xai_x_search_priority_european_grid_infrastructure"]["tool"], "x_search")
        self.assertEqual(tasks["xai_x_search_priority_european_grid_infrastructure"]["provider"], "xai_grok")
        self.assertEqual(tasks["xai_human_hir_0099_x_search_robotics_suppliers"]["provider"], "xai_grok")
        self.assertEqual(tasks["xai_human_hir_0100_x_search_amd"]["provider"], "xai_grok")
        self.assertEqual(analysis_tasks["financial_compare_human_hir_0100_amd"]["tool"], "financial_compare")
        self.assertEqual(analysis_tasks["financial_review_human_hir_0100_amd"]["tool"], "financial_review")
        self.assertEqual(analysis_tasks["financial_review_human_hir_0100_amd"]["depends_on"], ["financial_compare_human_hir_0100_amd"])

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

def repo_state_for_manifest(
    current_rows=None,
    monitoring_rows=None,
    rejected_rows=None,
    priorities=None,
    human_requests=None,
) -> RepoState:
    root = REPO_ROOT
    return RepoState(
        root=root,
        stock_tables={
            "current_holdings": CsvTable(
                path=root / "stock_tracking/current_holdings/current_holdings.csv",
                fieldnames=[],
                rows=current_rows or [],
            ),
            "monitoring": CsvTable(
                path=root / "stock_tracking/monitoring/monitoring.csv",
                fieldnames=[],
                rows=monitoring_rows or [],
            ),
            "rejected": CsvTable(
                path=root / "stock_tracking/rejected/rejected.csv",
                fieldnames=[],
                rows=rejected_rows or [],
            ),
        },
        category_state_files={},
        stock_info_files={},
        human_requests=human_requests or [],
        research_priorities=priorities or [],
        human_review_items=[],
    )


if __name__ == "__main__":
    unittest.main()
