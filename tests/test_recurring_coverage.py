from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.recurring_coverage import (
    build_comparison_baseline,
    build_recurring_coverage,
    dated_freshness,
    load_coverage_config,
)
from stock_research.repo import CsvTable, RepoState, load_repo_state


REPO_ROOT = Path(__file__).resolve().parents[1]


class RecurringCoverageTests(unittest.TestCase):
    def test_current_repo_scope_maps_every_tracked_company_to_a_configured_cluster(self):
        state = load_repo_state(REPO_ROOT)

        coverage = build_recurring_coverage(state, date(2026, 8, 16))

        self.assertEqual(len(coverage["companies"]), 12)
        self.assertEqual(len(coverage["industry_clusters"]), 5)
        self.assertTrue(all(company["industry_cluster_ids"] for company in coverage["companies"]))
        self.assertTrue(
            all(
                cluster["mapping_source"] == "strategy/portfolio_industry_coverage.json"
                for cluster in coverage["industry_clusters"]
            )
        )
        self.assertEqual(coverage["impact_basis"], "membership_only")
        self.assertFalse(coverage["weights_available"])
        self.assertEqual(
            coverage["comparison_baseline"]["status"],
            "not_recorded",
        )
        self.assertTrue(coverage["comparison_baseline"]["latest_generated_run_id"])
        self.assertEqual(coverage["comparison_baseline"]["comparison_run_id"], "")
        self.assertFalse(coverage["comparison_baseline"]["latest_generated_is_accepted"])

    def test_overlapping_ticker_tags_share_clusters_without_duplicate_members(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_coverage_config(
                root,
                [
                    cluster("ai_infrastructure", "AI infrastructure", ["AAA", "BBB"]),
                    cluster("defense_edge", "Defense edge", ["AAA"]),
                ],
            )
            state = repo_state(
                root,
                current_rows=[company_row("AAA", "2026-08-10")],
                monitoring_rows=[company_row("BBB", "2026-07-01")],
            )

            coverage = build_recurring_coverage(state, date(2026, 8, 16))

        companies = {company["ticker"]: company for company in coverage["companies"]}
        clusters = {cluster_item["cluster_id"]: cluster_item for cluster_item in coverage["industry_clusters"]}
        self.assertEqual(companies["AAA"]["industry_cluster_ids"], ["ai_infrastructure", "defense_edge"])
        self.assertEqual(companies["BBB"]["industry_cluster_ids"], ["ai_infrastructure"])
        self.assertEqual(clusters["ai_infrastructure"]["member_tickers"], ["AAA", "BBB"])
        self.assertEqual(companies["AAA"]["freshness"]["metadata"]["status"], "within_recurring_window")
        self.assertEqual(companies["BBB"]["freshness"]["metadata"]["status"], "stale")

    def test_unmapped_company_gets_deterministic_csv_industry_fallback(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_coverage_config(root, [])
            state = repo_state(
                root,
                current_rows=[
                    {
                        **company_row("NEW", "2026-08-16"),
                        "sector": "Industrials",
                        "industry": "Specialty Machinery",
                    }
                ],
            )

            coverage = build_recurring_coverage(state, date(2026, 8, 16))

        company = coverage["companies"][0]
        cluster_item = coverage["industry_clusters"][0]
        self.assertEqual(company["industry_cluster_ids"], ["industry_specialty_machinery"])
        self.assertEqual(cluster_item["mapping_source"], "derived_from_stock_csv_industry")
        self.assertEqual(cluster_item["member_tickers"], ["NEW"])

    def test_latest_generated_run_is_not_used_without_explicit_acceptance(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "agents/runs/2026-08-01_weekly").mkdir(parents=True)
            (root / "agents/runs/2026-08-15_weekly").mkdir(parents=True)
            state_path = root / "agents/recurring_research_state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "portfolio_update": {
                            "accepted_run_id": "",
                            "accepted_at": "",
                            "accepted_by": "",
                        },
                    }
                ),
                encoding="utf-8",
            )

            baseline = build_comparison_baseline(root)

            self.assertEqual(baseline["latest_generated_run_id"], "2026-08-15_weekly")
            self.assertEqual(baseline["status"], "not_recorded")
            self.assertEqual(baseline["comparison_run_id"], "")

            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "portfolio_update": {
                            "accepted_run_id": "2026-08-01_weekly",
                            "accepted_at": "2026-08-02",
                            "accepted_by": "user",
                        },
                    }
                ),
                encoding="utf-8",
            )
            accepted = build_comparison_baseline(root)

        self.assertEqual(accepted["status"], "accepted")
        self.assertEqual(accepted["comparison_run_id"], "2026-08-01_weekly")
        self.assertFalse(accepted["latest_generated_is_accepted"])

    def test_freshness_distinguishes_missing_invalid_future_current_and_stale_dates(self):
        current_date = date(2026, 8, 16)

        self.assertEqual(dated_freshness("", current_date, 14)["status"], "unknown")
        self.assertEqual(dated_freshness("not-a-date", current_date, 14)["status"], "invalid_date")
        self.assertEqual(dated_freshness("2026-08-17", current_date, 14)["status"], "future_date")
        self.assertEqual(dated_freshness("2026-08-02", current_date, 14)["status"], "within_recurring_window")
        self.assertEqual(dated_freshness("2026-08-01", current_date, 14)["status"], "stale")

    def test_invalid_duplicate_cluster_ids_fail_closed(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_coverage_config(
                root,
                [
                    cluster("duplicate", "First", ["AAA"]),
                    cluster("duplicate", "Second", ["BBB"]),
                ],
            )

            with self.assertRaisesRegex(ValueError, "Duplicate portfolio industry cluster id"):
                load_coverage_config(root)


def cluster(cluster_id: str, label: str, tickers: list[str]) -> dict:
    return {
        "id": cluster_id,
        "label": label,
        "description": "Test cluster.",
        "ticker_tags": tickers,
        "industry_tags": [],
        "sector_tags": [],
        "themes": [],
        "exa_query": f"{label} latest developments",
        "grok_topic": f"{label} investor discussion",
    }


def company_row(ticker: str, updated: str) -> dict[str, str]:
    return {
        "ticker": ticker,
        "company_name": f"{ticker} Company",
        "sector": "Technology",
        "industry": "Computer Hardware",
        "date_last_updated": updated,
        "last_filing_checked": "",
        "last_news_checked": "",
        "last_sentiment_checked": "",
    }


def write_coverage_config(root: Path, clusters: list[dict]) -> None:
    path = root / "strategy/portfolio_industry_coverage.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": 1, "clusters": clusters}), encoding="utf-8")


def repo_state(
    root: Path,
    *,
    current_rows: list[dict[str, str]] | None = None,
    monitoring_rows: list[dict[str, str]] | None = None,
) -> RepoState:
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
                rows=[],
            ),
        },
        category_state_files={},
        stock_info_files={},
        human_requests=[],
        research_priorities=[],
        human_review_items=[],
    )


if __name__ == "__main__":
    unittest.main()
